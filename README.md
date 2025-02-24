# Evidence-Based Scheduling (EBS) GUI Application

This is a Python-based GUI application for Evidence-Based Scheduling (EBS), designed to help users manage tasks, estimate completion times, and analyze productivity using historical data. The application features a modern, user-friendly interface built with `customtkinter` and includes data visualization with `matplotlib`.

## Features

- **Add Tasks**: Input task names and estimated hours to track new tasks.
- **Complete Tasks**: Record actual hours for tasks, calculate velocity (estimated/actual time ratio), and update progress.
- **Modify Tasks**: Edit task names, estimated hours, and actual hours for existing tasks.
- **Predict Completion Time**: Estimate total time to complete a set of tasks based on average velocity.
- **Data Analysis**: Display statistics like average velocity, task completion rate, and visualize estimation errors and velocity trends via charts.

## Requirements

- Python 3.8 or higher
- `customtkinter` (install with `pip install customtkinter`)
- `matplotlib` (install with `pip install matplotlib`)

## Installation

1. Clone or download this repository to your local machine.
2. Ensure Python is installed on your system (check with `python --version`).
3. Install required packages by running:
```bash
pip install customtkinter matplotlib
```

4. Ensure your system has a Chinese font (e.g., Microsoft YaHei) installed for proper display of Chinese characters in charts. On Windows, this is typically available by default, but you can verify or install it via system settings or download from Microsoft’s website.

## Usage

1. Save the script as `ebs_gui_fixed_color_updated.py`.
2. Run the application with:

```bash
python ebs_gui_fixed_color_updated.py
```

3. Use the tabbed interface to:
- Add new tasks with names and estimated hours.
- Complete tasks by selecting from a scrollable list of unfinished tasks, entering actual hours, and submitting.
- Modify existing tasks by selecting from a dropdown, updating details, and saving.
- Predict total completion time for a set of tasks based on estimated hours.
- View data analysis for velocity, completion rates, and error trends in charts.
4. Data is automatically saved to `ebs_data.json` and loaded on startup for persistence.

## Notes

- The application uses a dark mode theme with a blue color scheme for a modern look.
- Tasks are stored in a JSON file (`ebs_data.json`) in the same directory as the script.
- Ensure proper font settings for Chinese characters in `matplotlib` plots by configuring `plt.rcParams` as shown in the code (using Microsoft YaHei).
- The “Complete Tasks” tab features a scrollable list of unfinished tasks, where clicking a task highlights it in blue until another is selected, providing clear visual feedback.

## Troubleshooting

- If the GUI doesn’t display properly, ensure all dependencies are installed and compatible with your Python version.
- If charts show squares or question marks instead of Chinese text, install Microsoft YaHei font and update `plt.rcParams` in the script.
- If errors occur with task data, check `ebs_data.json` for correct JSON format or delete it to start fresh.

## Contributing

This project is open for contributions. Feel free to fork the repository, make improvements, and submit pull requests. Issues or suggestions can be reported via the project’s issue tracker (if hosted on a platform like GitHub).

## License

This project is licensed under the MIT License - see the LICENSE file for details (if applicable, or specify your license here).
