/*
 * Alice Exynos8895 M2 conditional boost controller
 *
 * Normal M2 ceiling: 2314 MHz
 * Burst ceiling:     2704 MHz
 * Trigger:           A53 average busy >= 85% and A53 cluster >= 2.0 GHz
 * Burst budget:      180 ms in a rolling 480 ms window (37.5%)
 * Thermal guard:     deny boost at >= 65 C, re-arm below 62 C
 * Battery budget:    design >= 3200 mAh and remaining >= 1200 mAh
 *
 * The controller changes only the M2 maximum QoS. schedutil remains responsible
 * for selecting the actual M2 frequency; no minimum frequency is forced.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/workqueue.h>
#include <linux/cpufreq.h>
#include <linux/cpu.h>
#include <linux/thermal.h>
#include <linux/power_supply.h>
#include <linux/pm_qos.h>
#include <linux/jiffies.h>
#include <linux/mutex.h>

#define ALICE_M2_NORMAL_KHZ		2314000U
#define ALICE_M2_BOOST_KHZ		2704000U
#define ALICE_A53_LOAD_PCT		85U
#define ALICE_A53_NEAR_MAX_KHZ		2000000U
#define ALICE_BURST_MS			180U
#define ALICE_WINDOW_MS			480U
#define ALICE_THERMAL_OFF_MC		65000
#define ALICE_THERMAL_REARM_MC		62000
#define ALICE_BATT_REMAIN_UAH		1200000LL
#define ALICE_BATT_DESIGN_UAH		3200000LL
#define ALICE_POLL_MS			20U

static struct delayed_work alice_boost_work;
static struct thermal_zone_device *alice_thermal;
static DEFINE_MUTEX(alice_lock);
static u64 prev_idle[4];
static u64 prev_wall[4];
static bool have_sample;
static bool boosted;
static unsigned long window_start;
static unsigned int boost_used_ms;
static unsigned long boost_started;
static bool thermal_blocked;
static struct pm_qos_request alice_m2_max_qos;

static unsigned int alice_a53_load(void)
{
	unsigned int cpu, valid = 0;
	u64 idle, wall, didle, dwall;
	u64 busy_sum = 0;

	for (cpu = 0; cpu < 4; cpu++) {
		idle = get_cpu_idle_time(cpu, &wall, 0);
		if (idle == (u64)-1 || !wall)
			continue;
		if (!have_sample) {
			prev_idle[cpu] = idle;
			prev_wall[cpu] = wall;
			continue;
		}
		didle = idle - prev_idle[cpu];
		dwall = wall - prev_wall[cpu];
		prev_idle[cpu] = idle;
		prev_wall[cpu] = wall;
		if (!dwall)
			continue;
		if (didle > dwall)
			didle = dwall;
		busy_sum += 100 - (didle * 100 / dwall);
		valid++;
	}
	have_sample = true;
	return valid ? (unsigned int)(busy_sum / valid) : 0;
}

static bool alice_a53_near_max(void)
{
	unsigned int cpu, freq, min_freq = ~0U;
	for (cpu = 0; cpu < 4; cpu++) {
		freq = cpufreq_quick_get(cpu);
		if (!freq)
			return false;
		if (freq < min_freq)
			min_freq = freq;
	}
	return min_freq >= ALICE_A53_NEAR_MAX_KHZ;
}

static bool alice_thermal_ok(void)
{
	int temp = 0;
	int ret;
	if (!alice_thermal)
		alice_thermal = thermal_zone_get_zone_by_name("APO_THERMAL");
	if (IS_ERR_OR_NULL(alice_thermal))
		return true;
	ret = thermal_zone_get_temp(alice_thermal, &temp);
	if (ret)
		return true;
	if (temp >= ALICE_THERMAL_OFF_MC) {
		thermal_blocked = true;
		return false;
	}
	if (thermal_blocked) {
		if (temp > ALICE_THERMAL_REARM_MC)
			return false;
		thermal_blocked = false;
	}
	return true;
}

static bool alice_battery_ok(void)
{
	struct power_supply *psy;
	union power_supply_propval now, design;
	int ret_now, ret_design;
	psy = power_supply_get_by_name("battery");
	if (!psy)
		return true;
	ret_now = power_supply_get_property(psy, POWER_SUPPLY_PROP_CHARGE_NOW, &now);
	ret_design = power_supply_get_property(psy, POWER_SUPPLY_PROP_CHARGE_FULL_DESIGN, &design);
	power_supply_put(psy);
	if (ret_now || ret_design || now.intval <= 0 || design.intval <= 0)
		return true;
	return (s64)design.intval >= ALICE_BATT_DESIGN_UAH &&
	       (s64)now.intval >= ALICE_BATT_REMAIN_UAH;
}

static void alice_set_boost(bool on)
{
	unsigned long elapsed;
	if (on == boosted)
		return;
	if (!on && boosted) {
		elapsed = jiffies_to_msecs(jiffies - boost_started);
		if (elapsed > ALICE_BURST_MS)
			elapsed = ALICE_BURST_MS;
		boost_used_ms = min(ALICE_BURST_MS,
			boost_used_ms + (unsigned int)elapsed);
	}
	/* This is a maximum-frequency QoS change only. schedutil still chooses the OPP. */
	pm_qos_update_request(&alice_m2_max_qos,
		on ? ALICE_M2_BOOST_KHZ : ALICE_M2_NORMAL_KHZ);
	boosted = on;
	if (on)
		boost_started = jiffies;
}

static bool alice_duty_allows(unsigned long now)
{
	unsigned long window_j = msecs_to_jiffies(ALICE_WINDOW_MS);
	if (time_after_eq(now, window_start + window_j)) {
		window_start = now;
		boost_used_ms = 0;
	}
	return boost_used_ms < ALICE_BURST_MS;
}

static void alice_account_boost(unsigned long now)
{
	unsigned long elapsed;
	if (!boosted)
		return;
	elapsed = jiffies_to_msecs(now - boost_started);
	if (elapsed >= ALICE_BURST_MS)
		alice_set_boost(false);
}

static int alice_cpu_notifier(struct notifier_block *nb,
				      unsigned long action, void *hcpu)
{
	unsigned int cpu = (unsigned long)hcpu;
	if (cpu < 4 || cpu > 7)
		return NOTIFY_OK;
	switch (action) {
	case CPU_DOWN_PREPARE:
#ifdef CPU_DOWN_PREPARE_FROZEN
	case CPU_DOWN_PREPARE_FROZEN:
#endif
		pr_info("alice_m2: refusing offline of M2 cpu%u\n", cpu);
		return NOTIFY_BAD;
	default:
		return NOTIFY_OK;
	}
}

static struct notifier_block alice_cpu_nb = {
	.notifier_call = alice_cpu_notifier,
};

static void alice_boost_worker(struct work_struct *work)
{
	unsigned long now = jiffies;
	unsigned int load;
	bool trigger;
	mutex_lock(&alice_lock);
	if (!window_start)
		window_start = now;
	alice_account_boost(now);
	load = alice_a53_load();
	trigger = load >= ALICE_A53_LOAD_PCT &&
		  alice_a53_near_max() &&
		  alice_thermal_ok() &&
		  alice_battery_ok();
	if (!alice_thermal_ok())
		trigger = false;
	if (boosted) {
		if (!trigger)
			alice_set_boost(false);
	} else if (trigger && alice_duty_allows(now)) {
		alice_set_boost(true);
	}
	mutex_unlock(&alice_lock);
	schedule_delayed_work(&alice_boost_work,
		msecs_to_jiffies(ALICE_POLL_MS));
}

static int __init alice_m2_boost_init(void)
{
	pm_qos_add_request(&alice_m2_max_qos, PM_QOS_CLUSTER1_FREQ_MAX,
		ALICE_M2_NORMAL_KHZ);
	register_cpu_notifier(&alice_cpu_nb);
	INIT_DELAYED_WORK(&alice_boost_work, alice_boost_worker);
	schedule_delayed_work(&alice_boost_work, msecs_to_jiffies(250));
	pr_info("alice_m2: 2314 normal / 2704 guarded burst; A53>=85%% and >=2GHz\n");
	return 0;
}
late_initcall(alice_m2_boost_init);

static void __exit alice_m2_boost_exit(void)
{
	cancel_delayed_work_sync(&alice_boost_work);
	alice_set_boost(false);
	pm_qos_remove_request(&alice_m2_max_qos);
	unregister_cpu_notifier(&alice_cpu_nb);
}
module_exit(alice_m2_boost_exit);

MODULE_DESCRIPTION("Alice Exynos8895 M2 conditional boost controller");
MODULE_LICENSE("GPL");
