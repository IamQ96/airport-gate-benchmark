from src.core.airport_config import load_airport_config

cfg = load_airport_config("configs/airport_waw_v1.yaml")

print("Loaded:", cfg.model_id)
print(cfg.airport_code, "-", cfg.airport_name)
print("Timezone:", cfg.timezone, "| Resolution(min):", cfg.resolution_minutes)
print("Buffer(min):", cfg.turnaround.buffer_minutes)
print("Default turnaround:", cfg.turnaround.default_turnaround_minutes)
print("Gates:")
for g in cfg.gates:
    print(" ", g.gate_id, g.compatible_classes, "walk_cost=", g.walk_cost)
