import json
from collections import defaultdict, OrderedDict
from datetime import datetime

def aggregate_stage_durations(input_file, output_file):
    """
    Reads the stage_durations.json file, aggregates step durations and counts per month,
    converts total duration in seconds to minutes, sorts steps by duration (descending),
    and outputs the results to month_summary.json.
    """
    # Load stage_durations.json
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Aggregate step durations and counts by month and step name.
    monthly_summary = defaultdict(lambda: defaultdict(lambda: {"duration": 0.0, "count": 0}))
    
    for item in data:
        # Only process items that have both a 'started_at' timestamp and a 'step_name'
        started_at = item.get("started_at")
        step_name = item.get("step_name")
        duration = item.get("duration_seconds", 0)
        
        if started_at and step_name:
            try:
                month_key = datetime.strptime(started_at, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m')
            except ValueError:
                continue  # Skip if the date format is unexpected
            monthly_summary[month_key][step_name]["duration"] += duration
            monthly_summary[month_key][step_name]["count"] += 1

    # Convert duration from seconds to minutes and sort step entries by duration_minutes (descending)
    monthly_summary_minutes = {}
    for month, steps in monthly_summary.items():
        steps_in_minutes = {
            step: {
                "duration_minutes": metrics["duration"] / 60.0,
                "count": metrics["count"]
            }
            for step, metrics in steps.items()
        }
        # Sort the steps by duration_minutes in descending order and store in an OrderedDict
        sorted_steps = OrderedDict(
            sorted(steps_in_minutes.items(), key=lambda kv: kv[1]["duration_minutes"], reverse=True)
        )
        monthly_summary_minutes[month] = sorted_steps

    # Write the aggregated output to the output file
    with open(output_file, 'w') as f:
        json.dump(monthly_summary_minutes, f, indent=4)

def main():
    input_file = 'stage_durations.json'
    output_file = 'month_summary.json'
    aggregate_stage_durations(input_file, output_file)
    print(f"Monthly summary written to {output_file}")

if __name__ == "__main__":
    main()