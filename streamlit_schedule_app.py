
import streamlit as st
import calendar
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date, timedelta
from io import BytesIO

# Shift label logic
def get_shift_label(date_obj, is_workday):
    if not is_workday:
        return "OFF"
    weekday = date_obj.weekday()
    if weekday == 1:
        return "11:30–7:30"
    elif weekday == 5:
        return "6:00–1:30"
    else:
        return "7:30–3:30"

# Generate schedule logic
def generate_schedule_mapping(year, month, last_worked_saturday):
    cal = calendar.Calendar(firstweekday=0)
    month_calendar = cal.monthdatescalendar(year, month)

    sat_list = []
    curr_sat = last_worked_saturday + timedelta(days=7)
    while curr_sat.month == month:
        sat_list.append(curr_sat)
        curr_sat += timedelta(days=14)

    first_saturday_of_month = min([d for week in month_calendar for d in week if d.weekday() == 5 and d.month == month])
    if first_saturday_of_month < min(sat_list):
        sat_list.insert(0, first_saturday_of_month)

    off_saturdays = []
    day = first_saturday_of_month
    while day.month == month:
        if day not in sat_list:
            off_saturdays.append(day)
        day += timedelta(days=7)

    schedule_mapping = {}
    for week in month_calendar:
        week_dates = [d for d in week if d.month == month]
        saturday = [d for d in week_dates if d.weekday() == 5]

        if not saturday:
            continue

        sat_date = saturday[0]
        if sat_date in off_saturdays:
            for day in week_dates:
                if day.weekday() in [5, 6]:
                    schedule_mapping[day] = False
                else:
                    schedule_mapping[day] = True
            next_monday = sat_date + timedelta(days=(7 - sat_date.weekday()) % 7)
            if next_monday.month == month:
                schedule_mapping[next_monday] = False
        else:
            for day in week_dates:
                if day.weekday() in [1, 2, 3, 4, 5]:
                    schedule_mapping[day] = True
                else:
                    schedule_mapping[day] = False

    return schedule_mapping, month_calendar

# PDF creation
def create_schedule_pdf(year, month, last_worked_saturday):
    schedule_mapping, month_calendar = generate_schedule_mapping(year, month, last_worked_saturday)
    buffer = BytesIO()

    with PdfPages(buffer) as pdf:
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_xlim(0, 7)
        ax.set_ylim(0, len(month_calendar))
        ax.axis('off')

        for i, day_name in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            ax.add_patch(plt.Rectangle((i, len(month_calendar) - 0.5), 1, 0.5, color='#f0f0f0'))
            ax.text(i + 0.5, len(month_calendar) - 0.25, day_name, ha='center', va='center', fontsize=13, weight='bold')

        for week_num, week in enumerate(month_calendar):
            for day_idx, day in enumerate(week):
                if day.month == month:
                    is_work = schedule_mapping.get(day, False)
                    color = '#a8e6a3' if is_work else '#f7a8a8'
                    shift_label = get_shift_label(day, is_work)

                    ax.add_patch(plt.Rectangle((day_idx, len(month_calendar) - week_num - 1), 1, 1, color=color, ec='white'))
                    ax.text(day_idx + 0.05, len(month_calendar) - week_num - 0.05, str(day.day),
                            ha='left', va='top', fontsize=12, weight='bold')
                    ax.text(day_idx + 0.5, len(month_calendar) - week_num - 0.55, shift_label,
                            ha='center', va='center', fontsize=10, color='black')

        work_patch = mpatches.Patch(color='#a8e6a3', label='Work Day (with shift)')
        off_patch = mpatches.Patch(color='#f7a8a8', label='Day Off')
        ax.legend(handles=[work_patch, off_patch], loc='lower center', bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=12)

        plt.title(f'Work Schedule – {calendar.month_name[month]} {year}', fontsize=18, weight='bold')
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

    buffer.seek(0)
    return buffer

# Streamlit UI
st.title("📅 Interactive Work Schedule Generator")
st.write("Build your custom monthly work schedule based on alternating Saturdays.")

col1, col2 = st.columns(2)
with col1:
    selected_month = st.selectbox("Select Month", list(calendar.month_name)[1:], index=date.today().month - 1)
with col2:
    selected_year = st.number_input("Enter Year", min_value=2024, max_value=2100, value=date.today().year)

last_sat = st.date_input("Select the **most recent Saturday you worked** (even if it's last month):", value=date.today())

if st.button("Generate PDF"):
    month_num = list(calendar.month_name).index(selected_month)
    pdf_file = create_schedule_pdf(selected_year, month_num, last_sat)
    st.success(f"PDF for {selected_month} {selected_year} is ready!")

    st.download_button(
        label="📥 Download PDF",
        data=pdf_file,
        file_name=f"Work_Schedule_{selected_month}_{selected_year}.pdf",
        mime="application/pdf"
    )
