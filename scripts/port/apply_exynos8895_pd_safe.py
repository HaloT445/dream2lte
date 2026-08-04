#!/usr/bin/env python3
"""Install a boot-safe Exynos8895 generic power-domain provider."""

from pathlib import Path

PD_SOURCE = r'''// SPDX-License-Identifier: GPL-2.0
/*
 * Boot-safe Exynos8895 power-domain provider for Linux 4.19 bring-up.
 *
 * All domains are registered as always-on. Runtime power-off is deliberately
 * blocked until physical boot, storage and suspend evidence exists.
 */
#include <linux/init.h>
#include <linux/list.h>
#include <linux/of.h>
#include <linux/pm_domain.h>
#include <linux/slab.h>

/* Keep this provider independent from CAL private headers. */
extern int cal_pd_control(unsigned int id, int on);
extern int cal_pd_status(unsigned int id);

struct alice_exynos8895_pd {
    struct generic_pm_domain genpd;
    struct device_node *np;
    u32 cal_id;
    struct list_head node;
};

static LIST_HEAD(alice_exynos8895_pd_list);

static struct alice_exynos8895_pd *
alice_exynos8895_pd_from_genpd(struct generic_pm_domain *genpd)
{
    return container_of(genpd, struct alice_exynos8895_pd, genpd);
}

static int alice_exynos8895_pd_power_on(struct generic_pm_domain *genpd)
{
    struct alice_exynos8895_pd *pd = alice_exynos8895_pd_from_genpd(genpd);
    int status;
    int ret;

    status = cal_pd_status(pd->cal_id);
    if (status > 0)
        return 0;

    ret = cal_pd_control(pd->cal_id, 1);
    if (ret)
        pr_err("ALice-PD: failed to power on %s (cal_id=0x%x, ret=%d)\n",
               genpd->name, pd->cal_id, ret);
    return ret;
}

static int alice_exynos8895_pd_power_off(struct generic_pm_domain *genpd)
{
    pr_debug("ALice-PD: keep %s powered for BOOT_SAFE bring-up\n",
             genpd->name);
    return 0;
}

static struct alice_exynos8895_pd *
alice_exynos8895_pd_find(struct device_node *np)
{
    struct alice_exynos8895_pd *pd;

    list_for_each_entry(pd, &alice_exynos8895_pd_list, node)
        if (pd->np == np)
            return pd;
    return NULL;
}

static int __init alice_exynos8895_pd_register_one(struct device_node *np)
{
    struct alice_exynos8895_pd *pd;
    int ret;

    pd = kzalloc(sizeof(*pd), GFP_KERNEL);
    if (!pd)
        return -ENOMEM;

    ret = of_property_read_u32(np, "cal_id", &pd->cal_id);
    if (ret) {
        pr_err("ALice-PD: %pOF missing cal_id\n", np);
        kfree(pd);
        return ret;
    }

    pd->np = of_node_get(np);
    pd->genpd.name = kstrdup_const(np->name, GFP_KERNEL);
    if (!pd->genpd.name) {
        of_node_put(pd->np);
        kfree(pd);
        return -ENOMEM;
    }

    pd->genpd.power_on = alice_exynos8895_pd_power_on;
    pd->genpd.power_off = alice_exynos8895_pd_power_off;
    pd->genpd.flags = GENPD_FLAG_ALWAYS_ON;

    ret = pm_genpd_init(&pd->genpd, NULL, false);
    if (ret)
        goto err_name;

    ret = of_genpd_add_provider_simple(np, &pd->genpd);
    if (ret)
        goto err_genpd;

    list_add_tail(&pd->node, &alice_exynos8895_pd_list);
    pr_info("ALice-PD: registered always-on %s (cal_id=0x%x)\n",
            pd->genpd.name, pd->cal_id);
    return 0;

err_genpd:
    pm_genpd_remove(&pd->genpd);
err_name:
    kfree_const(pd->genpd.name);
    of_node_put(pd->np);
    kfree(pd);
    return ret;
}

static void __init alice_exynos8895_pd_link_parents(void)
{
    struct alice_exynos8895_pd *child;

    list_for_each_entry(child, &alice_exynos8895_pd_list, node) {
        struct alice_exynos8895_pd *parent;
        struct device_node *parent_np;
        int ret;

        parent_np = of_parse_phandle(child->np, "parent", 0);
        if (!parent_np)
            continue;

        parent = alice_exynos8895_pd_find(parent_np);
        if (!parent) {
            pr_warn("ALice-PD: parent %pOF for %s not registered\n",
                    parent_np, child->genpd.name);
            of_node_put(parent_np);
            continue;
        }

        ret = pm_genpd_add_subdomain(&parent->genpd, &child->genpd);
        if (ret)
            pr_warn("ALice-PD: cannot link %s -> %s: %d\n",
                    parent->genpd.name, child->genpd.name, ret);
        of_node_put(parent_np);
    }
}

static int __init alice_exynos8895_pd_init(void)
{
    struct device_node *np;
    unsigned int registered = 0;

    for_each_compatible_node(np, NULL, "samsung,exynos-pd") {
        int ret;

        if (!of_device_is_available(np))
            continue;
        ret = alice_exynos8895_pd_register_one(np);
        if (ret)
            pr_err("ALice-PD: failed to register %pOF: %d\n", np, ret);
        else
            registered++;
    }

    alice_exynos8895_pd_link_parents();
    pr_info("ALice-PD: BOOT_SAFE provider ready (%u domains)\n", registered);
    return registered ? 0 : -ENODEV;
}
arch_initcall(alice_exynos8895_pd_init);
'''


def main() -> None:
    output = Path("drivers/soc/samsung/exynos8895-pd-safe.c")
    output.write_text(PD_SOURCE)

    makefile = Path("drivers/soc/samsung/Makefile")
    text = makefile.read_text()
    marker = "obj-y += exynos8895-pd-safe.o"
    if marker not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += (
            "\n# ALice Exynos8895 BOOT_SAFE power-domain provider\n"
            "obj-y += exynos8895-pd-safe.o\n"
        )
        makefile.write_text(text)

    print("Exynos8895 BOOT_SAFE power-domain provider prepared")


if __name__ == "__main__":
    main()
