#!/usr/bin/env python3
"""Validate the stored planning polygon and its simple setback envelope."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def polygon_area(points):
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points))) / 2.0)

def load_plan():
    with (ROOT / 'site_plan.json').open(encoding='utf-8') as handle:
        return json.load(handle)

def buildable_envelope(plan):
    vertices = [(item['x'], item['y']) for item in plan['vertices']]
    min_x = min(x for x, _ in vertices)
    max_x = max(x for x, _ in vertices)
    min_y = min(y for _, y in vertices)
    max_y = max(y for _, y in vertices)
    step_x, step_y = vertices[2]
    s = plan['setbacks_ft']
    return [(min_x + s['west'], min_y + s['south']), (step_x - s['east'], min_y + s['south']), (step_x - s['east'], step_y + s['south']), (max_x - s['east'], step_y + s['south']), (max_x - s['east'], max_y - s['north']), (min_x + s['west'], max_y - s['north'])]

def main():
    plan = load_plan()
    plot = [(item['x'], item['y']) for item in plan['vertices']]
    envelope = buildable_envelope(plan)
    plot_area = polygon_area(plot)
    envelope_area = polygon_area(envelope)
    claimed = plan['planning_area_claimed_sqft_per_floor']
    print(f'Plot area from coordinates: {plot_area:.2f} sq ft')
    print(f'Simple setback-envelope area: {envelope_area:.2f} sq ft')
    print(f'Planning area carried from brief: {claimed:.2f} sq ft per floor')
    if abs(envelope_area - claimed) > 0.5:
        print('WARNING: calculated envelope differs from the brief; verify survey and true polygon offset.')
        return 1
    print('OK: stored area values are consistent within tolerance.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
