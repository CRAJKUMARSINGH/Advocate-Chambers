#!/usr/bin/env python3
"""Generate a visual and CAD-compatible setback envelope from site_plan.json."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load_site_plan(filepath):
    with Path(filepath).open(encoding='utf-8') as handle:
        return json.load(handle)

def as_points(items):
    return [(float(item['x']), float(item['y'])) for item in items]

def calculate_buildable_envelope(plot_vertices, setbacks):
    """Apply the brief's coordinate-based west/north/south/east setbacks."""
    min_x = min(x for x, _ in plot_vertices)
    max_x = max(x for x, _ in plot_vertices)
    min_y = min(y for _, y in plot_vertices)
    max_y = max(y for _, y in plot_vertices)
    step_x, step_y = plot_vertices[2]
    return [
        (min_x + setbacks['west'], min_y + setbacks['south']),
        (step_x - setbacks['east'], min_y + setbacks['south']),
        (step_x - setbacks['east'], step_y + setbacks['south']),
        (max_x - setbacks['east'], step_y + setbacks['south']),
        (max_x - setbacks['east'], max_y - setbacks['north']),
        (min_x + setbacks['west'], max_y - setbacks['north']),
    ]

def polygon_area(points):
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points))) / 2.0)

def plot_layout(plot_vertices, envelope_vertices, output_file):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 15))
    plot = plot_vertices + [plot_vertices[0]]
    envelope = envelope_vertices + [envelope_vertices[0]]
    plot_x, plot_y = zip(*plot)
    env_x, env_y = zip(*envelope)
    ax.plot(plot_x, plot_y, 'r-', linewidth=2, label='Plot boundary')
    ax.fill(env_x, env_y, color='lightgreen', alpha=0.4, label='Simple setback envelope')
    ax.plot(env_x, env_y, 'b--', linewidth=2)
    for index, (x, y) in enumerate(envelope_vertices, start=1):
        ax.text(x, y, f'P{index}', fontsize=11, ha='right', va='bottom', color='darkblue', fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlabel('East-West distance (ft)')
    ax.set_ylabel('North-South distance (ft)')
    ax.set_title('Bar Association Banswara - Site Plan and Setback Envelope')
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_file, dpi=240)
    plt.close(fig)

def generate_dxf(plot_vertices, envelope_vertices, filename):
    import ezdxf
    doc = ezdxf.new('R2010', setup=True)
    if 'PLOT_BOUNDARY' not in doc.layers:
        doc.layers.add('PLOT_BOUNDARY', color=1)
    if 'BUILDABLE_ENVELOPE' not in doc.layers:
        doc.layers.add('BUILDABLE_ENVELOPE', color=3)
    msp = doc.modelspace()
    msp.add_lwpolyline(plot_vertices, close=True, dxfattribs={'layer': 'PLOT_BOUNDARY'})
    msp.add_lwpolyline(envelope_vertices, close=True, dxfattribs={'layer': 'BUILDABLE_ENVELOPE'})
    doc.saveas(filename)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', default=str(ROOT / 'site_plan.json'))
    parser.add_argument('--output-dir', default=str(ROOT / 'generated'))
    args = parser.parse_args()
    plan = load_site_plan(args.json)
    plot = as_points(plan['vertices'])
    envelope = calculate_buildable_envelope(plot, plan['setbacks_ft'])
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print('Plot area: %.2f sq ft' % polygon_area(plot))
    print('Simple setback-envelope area: %.2f sq ft' % polygon_area(envelope))
    print('Planning area in brief: %.2f sq ft per floor' % plan['planning_area_claimed_sqft_per_floor'])
    plot_layout(plot, envelope, output_dir / 'site_plan_envelope.png')
    generate_dxf(plot, envelope, output_dir / 'bar_association_plan.dxf')
    print('Generated: ' + str(output_dir))

if __name__ == '__main__':
    main()
