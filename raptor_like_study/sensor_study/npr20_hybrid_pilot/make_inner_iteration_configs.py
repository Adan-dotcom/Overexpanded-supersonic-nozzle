from pathlib import Path


here = Path(__file__).resolve().parent
base = (here / "npr20_relax_SLAU2_dt025_to100us.cfg").read_text(encoding="ascii")

for inner in (10, 20, 30, 50):
    tag = f"inner{inner}_from500"
    config = base
    replacements = {
        "RESTART_ITER= 201": "RESTART_ITER= 501",
        "TIME_ITER= 3114": "TIME_ITER= 521",
        "INNER_ITER= 10": f"INNER_ITER= {inner}",
        "CONV_FILENAME= history_npr20_relax_SLAU2_dt025": f"CONV_FILENAME= history_npr20_{tag}",
        "RESTART_FILENAME= restart_npr20_relax_SLAU2_dt025": f"RESTART_FILENAME= restart_npr20_{tag}",
        "VOLUME_FILENAME= flow_npr20_relax_SLAU2_dt025": f"VOLUME_FILENAME= flow_npr20_{tag}",
        "SURFACE_FILENAME= wall_npr20_relax_SLAU2_dt025": f"SURFACE_FILENAME= wall_npr20_{tag}",
        "OUTPUT_WRT_FREQ= 50, 100, 10, 10": "OUTPUT_WRT_FREQ= 20, 20, 20, 20",
    }
    for old, new in replacements.items():
        if old not in config:
            raise ValueError(f"Missing template text: {old}")
        config = config.replace(old, new)
    (here / f"npr20_{tag}.cfg").write_text(config, encoding="ascii")

for cfl_tag, cfl in (("1", "1.0"), ("2", "2.0"), ("3", "3.0"), ("5", "5.0")):
    tag = f"cfl{cfl_tag}_inner30_from500"
    config = base
    replacements = {
        "RESTART_ITER= 201": "RESTART_ITER= 501",
        "TIME_ITER= 3114": "TIME_ITER= 521",
        "INNER_ITER= 10": "INNER_ITER= 30",
        "CFL_NUMBER= 0.5": f"CFL_NUMBER= {cfl}",
        "CONV_FILENAME= history_npr20_relax_SLAU2_dt025": f"CONV_FILENAME= history_npr20_{tag}",
        "RESTART_FILENAME= restart_npr20_relax_SLAU2_dt025": f"RESTART_FILENAME= restart_npr20_{tag}",
        "VOLUME_FILENAME= flow_npr20_relax_SLAU2_dt025": f"VOLUME_FILENAME= flow_npr20_{tag}",
        "SURFACE_FILENAME= wall_npr20_relax_SLAU2_dt025": f"SURFACE_FILENAME= wall_npr20_{tag}",
        "OUTPUT_WRT_FREQ= 50, 100, 10, 10": "OUTPUT_WRT_FREQ= 20, 20, 20, 20",
    }
    for old, new in replacements.items():
        if old not in config:
            raise ValueError(f"Missing template text: {old}")
        config = config.replace(old, new)
    (here / f"npr20_{tag}.cfg").write_text(config, encoding="ascii")

tag = "cfl2_inner50_from500"
config = base
replacements = {
    "RESTART_ITER= 201": "RESTART_ITER= 501",
    "TIME_ITER= 3114": "TIME_ITER= 521",
    "INNER_ITER= 10": "INNER_ITER= 50",
    "CFL_NUMBER= 0.5": "CFL_NUMBER= 2.0",
    "CONV_FILENAME= history_npr20_relax_SLAU2_dt025": f"CONV_FILENAME= history_npr20_{tag}",
    "RESTART_FILENAME= restart_npr20_relax_SLAU2_dt025": f"RESTART_FILENAME= restart_npr20_{tag}",
    "VOLUME_FILENAME= flow_npr20_relax_SLAU2_dt025": f"VOLUME_FILENAME= flow_npr20_{tag}",
    "SURFACE_FILENAME= wall_npr20_relax_SLAU2_dt025": f"SURFACE_FILENAME= wall_npr20_{tag}",
    "OUTPUT_WRT_FREQ= 50, 100, 10, 10": "OUTPUT_WRT_FREQ= 20, 20, 20, 20",
}
for old, new in replacements.items():
    if old not in config:
        raise ValueError(f"Missing template text: {old}")
    config = config.replace(old, new)
(here / f"npr20_{tag}.cfg").write_text(config, encoding="ascii")

production = base
for old, new in {
    "RESTART_ITER= 201": "RESTART_ITER= 521",
    "INNER_ITER= 10": "INNER_ITER= 30",
    "CFL_NUMBER= 0.5": "CFL_NUMBER= 2.0",
    "SOLUTION_FILENAME= restart_npr20_relax_SLAU2_dt025": "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500",
    "CONV_FILENAME= history_npr20_relax_SLAU2_dt025": "CONV_FILENAME= history_npr20_production_cfl2_i30_from520",
    "RESTART_FILENAME= restart_npr20_relax_SLAU2_dt025": "RESTART_FILENAME= restart_npr20_production_cfl2_i30_from520",
    "VOLUME_FILENAME= flow_npr20_relax_SLAU2_dt025": "VOLUME_FILENAME= flow_npr20_production_cfl2_i30_from520",
    "SURFACE_FILENAME= wall_npr20_relax_SLAU2_dt025": "SURFACE_FILENAME= wall_npr20_production_cfl2_i30_from520",
}.items():
    if old not in production:
        raise ValueError(f"Missing base template text: {old}")
    production = production.replace(old, new)
for dt_tag, dt_value, final_iteration in (("050", "5.0E-8", 721), ("100", "1.0E-7", 711)):
    bdf1_tag = f"dt{dt_tag}_cfl2_i30_bdf1_from700"
    bdf1 = production
    bdf1_replacements = {
        "RESTART_ITER= 521": "RESTART_ITER= 701",
        "TIME_MARCHING= DUAL_TIME_STEPPING-2ND_ORDER": "TIME_MARCHING= DUAL_TIME_STEPPING-1ST_ORDER",
        "TIME_STEP= 2.5E-8": f"TIME_STEP= {dt_value}",
        "TIME_ITER= 3114": "TIME_ITER= 703",
        "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500": "SOLUTION_FILENAME= restart_npr20_production_cfl2_i30_from520",
        "CONV_FILENAME= history_npr20_production_cfl2_i30_from520": f"CONV_FILENAME= history_npr20_{bdf1_tag}",
        "RESTART_FILENAME= restart_npr20_production_cfl2_i30_from520": f"RESTART_FILENAME= restart_npr20_{bdf1_tag}",
        "VOLUME_FILENAME= flow_npr20_production_cfl2_i30_from520": f"VOLUME_FILENAME= flow_npr20_{bdf1_tag}",
        "SURFACE_FILENAME= wall_npr20_production_cfl2_i30_from520": f"SURFACE_FILENAME= wall_npr20_{bdf1_tag}",
        "OUTPUT_WRT_FREQ= 50, 100, 10, 10": "OUTPUT_WRT_FREQ= 1, 2, 2, 2",
    }
    for old, new in bdf1_replacements.items():
        if old not in bdf1:
            raise ValueError(f"Missing production template text: {old}")
        bdf1 = bdf1.replace(old, new)
    (here / f"npr20_{bdf1_tag}.cfg").write_text(bdf1, encoding="ascii")

    bdf2_tag = f"dt{dt_tag}_cfl2_i30_bdf2_from700"
    bdf2 = production
    bdf2_replacements = {
        "RESTART_ITER= 521": "RESTART_ITER= 703",
        "TIME_STEP= 2.5E-8": f"TIME_STEP= {dt_value}",
        "TIME_ITER= 3114": f"TIME_ITER= {final_iteration}",
        "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500": f"SOLUTION_FILENAME= restart_npr20_{bdf1_tag}",
        "CONV_FILENAME= history_npr20_production_cfl2_i30_from520": f"CONV_FILENAME= history_npr20_{bdf2_tag}",
        "RESTART_FILENAME= restart_npr20_production_cfl2_i30_from520": f"RESTART_FILENAME= restart_npr20_{bdf2_tag}",
        "VOLUME_FILENAME= flow_npr20_production_cfl2_i30_from520": f"VOLUME_FILENAME= flow_npr20_{bdf2_tag}",
        "SURFACE_FILENAME= wall_npr20_production_cfl2_i30_from520": f"SURFACE_FILENAME= wall_npr20_{bdf2_tag}",
        "OUTPUT_WRT_FREQ= 50, 100, 10, 10": f"OUTPUT_WRT_FREQ= {final_iteration - 703}, {final_iteration - 703}, {final_iteration - 703}, {final_iteration - 703}",
    }
    for old, new in bdf2_replacements.items():
        if old not in bdf2:
            raise ValueError(f"Missing production template text: {old}")
        bdf2 = bdf2.replace(old, new)
    (here / f"npr20_{bdf2_tag}.cfg").write_text(bdf2, encoding="ascii")

for ranks in (6, 12):
    tag = f"benchmark_np{ranks}_from520"
    config = base
    replacements = {
        "RESTART_ITER= 201": "RESTART_ITER= 521",
        "TIME_ITER= 3114": "TIME_ITER= 526",
        "INNER_ITER= 10": "INNER_ITER= 30",
        "CFL_NUMBER= 0.5": "CFL_NUMBER= 2.0",
        "SOLUTION_FILENAME= restart_npr20_relax_SLAU2_dt025": "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500",
        "CONV_FILENAME= history_npr20_relax_SLAU2_dt025": f"CONV_FILENAME= history_npr20_{tag}",
        "RESTART_FILENAME= restart_npr20_relax_SLAU2_dt025": f"RESTART_FILENAME= restart_npr20_{tag}",
        "VOLUME_FILENAME= flow_npr20_relax_SLAU2_dt025": f"VOLUME_FILENAME= flow_npr20_{tag}",
        "SURFACE_FILENAME= wall_npr20_relax_SLAU2_dt025": f"SURFACE_FILENAME= wall_npr20_{tag}",
        "OUTPUT_WRT_FREQ= 50, 100, 10, 10": "OUTPUT_WRT_FREQ= 5, 5, 5, 5",
    }
    for old, new in replacements.items():
        if old not in config:
            raise ValueError(f"Missing template text: {old}")
        config = config.replace(old, new)
    (here / f"npr20_{tag}.cfg").write_text(config, encoding="ascii")

tag = "production_cfl2_i30_from520"
config = base
replacements = {
    "RESTART_ITER= 201": "RESTART_ITER= 521",
    "INNER_ITER= 10": "INNER_ITER= 30",
    "CFL_NUMBER= 0.5": "CFL_NUMBER= 2.0",
    "SOLUTION_FILENAME= restart_npr20_relax_SLAU2_dt025": "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500",
    "CONV_FILENAME= history_npr20_relax_SLAU2_dt025": f"CONV_FILENAME= history_npr20_{tag}",
    "RESTART_FILENAME= restart_npr20_relax_SLAU2_dt025": f"RESTART_FILENAME= restart_npr20_{tag}",
    "VOLUME_FILENAME= flow_npr20_relax_SLAU2_dt025": f"VOLUME_FILENAME= flow_npr20_{tag}",
    "SURFACE_FILENAME= wall_npr20_relax_SLAU2_dt025": f"SURFACE_FILENAME= wall_npr20_{tag}",
}
for old, new in replacements.items():
    if old not in config:
        raise ValueError(f"Missing template text: {old}")
    config = config.replace(old, new)
(here / f"npr20_{tag}.cfg").write_text(config, encoding="ascii")

resume = production.replace("RESTART_ITER= 521", "RESTART_ITER= 701")
resume = resume.replace(
    "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500",
    "SOLUTION_FILENAME= restart_npr20_production_cfl2_i30_from520",
)
(here / "npr20_production_cfl2_i30_resume_from700.cfg").write_text(resume, encoding="ascii")

extended = production.replace("RESTART_ITER= 521", "RESTART_ITER= 3114")
extended = extended.replace("TIME_ITER= 3114", "TIME_ITER= 4814")
extended = extended.replace(
    "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500",
    "SOLUTION_FILENAME= restart_npr20_production_cfl2_i30_from520",
)
(here / "npr20_production_cfl2_i30_extend_to143us.cfg").write_text(extended, encoding="ascii")

settling = production.replace("RESTART_ITER= 521", "RESTART_ITER= 4814")
settling = settling.replace("TIME_ITER= 3114", "TIME_ITER= 5614")
settling = settling.replace(
    "SOLUTION_FILENAME= restart_npr20_cfl2_inner30_from500",
    "SOLUTION_FILENAME= restart_npr20_production_cfl2_i30_from520",
)
(here / "npr20_production_cfl2_i30_settle_to163us.cfg").write_text(settling, encoding="ascii")
