import pandas as pd
import solara
import matplotlib.pyplot as plt
import numpy as np

# Load the CSV file
file_path = 'solara-dropdown.csv'
data = pd.read_csv(file_path)

# Extract unique states
unique_states = data['state'].unique().tolist()

# Reactive variables
selected_state = solara.reactive(unique_states[0])
selected_name = solara.reactive("")
generate_trigger = solara.reactive(0)

# Function to filter data based on selected state
def get_filtered_names(state):
    filtered_names = data[data['state'] == state]['Name'].unique().tolist()
    if filtered_names:
        selected_name.value = filtered_names[0]
    return filtered_names

# Function to plot bar chart using matplotlib
def plot_bar_chart(df, name):
    filtered_data = df[df['Name'] == name]
    if filtered_data.empty:
        print("No data available for the selected filters.")
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    width = 0.3  # Bar width
    x = np.arange(len(filtered_data))  # the label locations
    ax.bar(x - width/2, filtered_data['XCoordinate'], width, label='XCoordinate', color='blue')
    ax.bar(x + width/2, filtered_data['YCoordinate'], width, label='YCoordinate', color='orange', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(filtered_data['Name'], rotation=45, ha='right')
    ax.set_xlabel('Name', fontweight='bold')
    ax.set_ylabel('Coordinate Value', fontweight='bold')
    ax.set_title(f'Bar Chart for {name}', fontweight='bold')
    ax.legend(loc='upper right')
    
    # Add data labels
    for i in range(len(filtered_data)):
        ax.text(i - width/2, filtered_data['XCoordinate'].iloc[i] / 2, str(filtered_data['XCoordinate'].iloc[i]), ha='center', va='bottom', color='white')
        ax.text(i + width/2, filtered_data['YCoordinate'].iloc[i] / 2, str(filtered_data['YCoordinate'].iloc[i]), ha='center', va='bottom', color='black')
    
    fig.tight_layout()  # Adjust layout to make room for rotated x-tick labels
    return fig

# Components
@solara.component
def View():
    if generate_trigger.value > 0 and selected_name.value:
        fig = plot_bar_chart(data, selected_name.value)
        if fig:
            with solara.VBox() as main:
                solara.FigureMatplotlib(fig)
            solara.Info("Chart has been updated.")
        else:
            solara.Warning("No data available for the selected state and name")
    else:
        solara.Warning("Please select a state and a name.")

@solara.component
def Controls():
    # Update the options for the Name dropdown based on the selected state
    filtered_names = get_filtered_names(selected_state.value)
    
    solara.Select('State', values=unique_states, value=selected_state)
    solara.Select('Name', values=filtered_names, value=selected_name)
    
    def generate_chart():
        print(f"Generating chart for state: {selected_state.value} and name: {selected_name.value}")
        generate_trigger.value += 1

    solara.Button(label="Generate Chart", on_click=generate_chart, icon_name="mdi-chart-bar")

@solara.component
def Page():
    with solara.Sidebar():
        Controls()
    View()

# Display the page
Page()
