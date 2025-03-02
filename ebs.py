import customtkinter as ctk
from tkinter import messagebox
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Global constants
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 650
TAB_FRAME_WIDTH = 450
TAB_FRAME_HEIGHT = 650

# Set matplotlib font for Chinese support
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# Data file
DATA_FILE = "ebs_data.json"

# Load or initialize data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure each task has a "time_segments" field
            for task in data["tasks"]:
                if "time_segments" not in task:
                    task["time_segments"] = []
                    if task["actual_hours"] is not None:
                        task["time_segments"].append({
                            "hours": task["actual_hours"],
                            "timestamp": task.get("end_time", datetime.now().isoformat())
                        })
            return data
    return {"tasks": [], "velocity": 1.0}

# Save data to file
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Update velocity based on completed tasks
def update_velocity(data):
    completed = [t for t in data["tasks"] if t.get("completed", False) and t["time_segments"]]
    if completed:
        total_velocity = sum(t["estimated_hours"] / sum(segment["hours"] for segment in t["time_segments"]) for t in completed)
        data["velocity"] = total_velocity / len(completed)
    save_data(data)

# Analyze data for statistics
def analyze_data(data):
    completed = [t for t in data["tasks"] if t.get("completed", False) and t["time_segments"]]
    avg_velocity = data["velocity"] if completed else 1.0
    completion_rate = (len(completed) / len(data["tasks"]) * 100) if data["tasks"] else 0.0
    estimated = [t["estimated_hours"] for t in completed]
    actual = [sum(segment["hours"] for segment in t["time_segments"]) for t in completed]
    errors = [(e - a) / e * 100 if e > 0 else 0 for e, a in zip(estimated, actual)]
    return avg_velocity, completion_rate, estimated, actual, errors

# Main GUI class
class EBSSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Evidence-Based Scheduling")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(True, True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.data = load_data()

        # Create tab view
        self.notebook = ctk.CTkTabview(root, width=580, height=360)
        self.notebook.pack(pady=10, padx=10)

        # Add tabs
        self.notebook.add("添加任務")
        self.notebook.add("記錄工作時間")
        self.notebook.add("完成任務")
        self.notebook.add("修改任務")
        self.notebook.add("預測時間")
        self.notebook.add("數據分析")

        self.selected_finish_task_name = None
        self.selected_record_task_name = None

        # Initialize tabs
        self.create_add_tab()
        self.create_record_time_tab()
        self.create_finish_tab()
        self.create_modify_tab()
        self.create_predict_tab()
        self.create_analyze_tab()

    ### Add Task Tab ###
    def create_add_tab(self):
        frame = ctk.CTkScrollableFrame(self.notebook.tab("添加任務"), width=TAB_FRAME_WIDTH, height=TAB_FRAME_HEIGHT)
        frame.pack(pady=5, padx=5, fill="both", expand=True)
        ctk.CTkLabel(frame, text="任務名稱:").pack(pady=5)
        self.task_name = ctk.CTkEntry(frame, width=200)
        self.task_name.pack(pady=5)
        ctk.CTkLabel(frame, text="估計時間 (小時):").pack(pady=5)
        self.estimated_hours = ctk.CTkEntry(frame, width=100)
        self.estimated_hours.pack(pady=5)
        ctk.CTkButton(frame, text="添加任務", command=self.add_task).pack(pady=5)

    def add_task(self):
        name = self.task_name.get().strip()
        try:
            hours = float(self.estimated_hours.get())
            if not name or hours <= 0:
                messagebox.showerror("錯誤", "任務名稱和估計時間必須有效！")
                return
            # Check for duplicate task name
            if any(task["name"] == name for task in self.data["tasks"]):
                messagebox.showerror("錯誤", "任務名稱已存在！")
                return
            task = {
                "name": name,
                "estimated_hours": hours,
                "actual_hours": None,
                "time_segments": [],
                "start_time": datetime.now().isoformat(),
                "completed": False
            }
            self.data["tasks"].append(task)
            save_data(self.data)
            self.update_task_listbox()
            self.update_finish_tasks()
            self.update_record_tasks()
            self.task_name.delete(0, ctk.END)
            self.estimated_hours.delete(0, ctk.END)
            messagebox.showinfo("成功", f"任務 '{name}' 添加成功！")
        except ValueError:
            messagebox.showerror("錯誤", "估計時間必須是數字！")

    ### Record Time Tab ###
    def create_record_time_tab(self):
        frame = ctk.CTkScrollableFrame(self.notebook.tab("記錄工作時間"), width=TAB_FRAME_WIDTH, height=TAB_FRAME_HEIGHT)
        frame.pack(pady=5, padx=5, fill="both", expand=True)
        scroll_frame = ctk.CTkScrollableFrame(frame, width=200, height=150)
        scroll_frame.pack(pady=5, padx=5)
        self.record_tasks = ctk.CTkFrame(scroll_frame)
        self.record_tasks.pack(fill="both", expand=True)
        self.update_record_tasks()
        ctk.CTkLabel(frame, text="已記錄時間段:").pack(pady=5)
        container_frame = ctk.CTkFrame(frame, width=200, height=150)
        container_frame.pack(pady=5, padx=5)
        container_frame.pack_propagate(False)
        self.segments_frame = ctk.CTkScrollableFrame(container_frame, width=200)
        self.segments_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="本次工作時間 (小時):").pack(pady=5)
        self.record_hours = ctk.CTkEntry(frame, width=100)
        self.record_hours.pack(pady=5)
        ctk.CTkButton(frame, text="記錄時間", command=self.record_time).pack(pady=5)

    def update_record_tasks(self):
        all_tasks = [task["name"] for task in self.data["tasks"]]
        for widget in self.record_tasks.winfo_children():
            widget.destroy()
        self.record_task_var = ctk.StringVar(value=self.selected_record_task_name or "")
        for task_name in all_tasks:
            radio = ctk.CTkRadioButton(
                self.record_tasks, text=task_name, variable=self.record_task_var, value=task_name,
                command=lambda name=task_name: self.select_record_task(name),
                fg_color="#4a6cd4", hover_color="#3a5cbd", border_color="#d1d1d1"
            )
            radio.pack(pady=2)
        self.record_tasks.update_idletasks()

    def select_record_task(self, name):
        self.selected_record_task_name = name
        self.record_task_var.set(name)
        self.update_time_segments_display()

    def update_time_segments_display(self):
        for widget in self.segments_frame.winfo_children():
            widget.destroy()
        if not self.selected_record_task_name:
            return
        for task in self.data["tasks"]:
            if task["name"] == self.selected_record_task_name:
                total_time = sum(segment["hours"] for segment in task["time_segments"])
                if task["time_segments"]:
                    ctk.CTkLabel(self.segments_frame, text=f"總計時間: {total_time:.2f} 小時").pack(pady=2)
                for i, segment in enumerate(task["time_segments"]):
                    time_str = datetime.fromisoformat(segment["timestamp"]).strftime("%Y-%m-%d %H:%M")
                    ctk.CTkLabel(self.segments_frame, text=f"{i+1}. {segment['hours']:.2f} 小時 ({time_str})").pack(pady=1)
                break

    def record_time(self):
        if not self.selected_record_task_name:
            messagebox.showerror("錯誤", "請選擇一個任務！")
            return
        try:
            hours = float(self.record_hours.get())
            if hours <= 0:
                messagebox.showerror("錯誤", "工作時間必須大於0！")
                return
            for task in self.data["tasks"]:
                if task["name"] == self.selected_record_task_name:
                    task["time_segments"].append({"hours": hours, "timestamp": datetime.now().isoformat()})
                    task["actual_hours"] = sum(segment["hours"] for segment in task["time_segments"])
                    task["end_time"] = datetime.now().isoformat()
                    update_velocity(self.data)
                    save_data(self.data)
                    self.record_hours.delete(0, ctk.END)
                    self.update_time_segments_display()
                    messagebox.showinfo("成功", f"已為任務 '{self.selected_record_task_name}' 記錄 {hours:.2f} 小時工作時間")
                    break
        except ValueError:
            messagebox.showerror("錯誤", "工作時間必須是數字！")

    ### Finish Task Tab ###
    def create_finish_tab(self):
        frame = ctk.CTkScrollableFrame(self.notebook.tab("完成任務"), width=TAB_FRAME_WIDTH, height=TAB_FRAME_HEIGHT)
        frame.pack(pady=5, padx=5, fill="both", expand=True)
        scroll_frame = ctk.CTkScrollableFrame(frame, width=200, height=150)
        scroll_frame.pack(pady=5, padx=5)
        self.finish_tasks = ctk.CTkFrame(scroll_frame)
        self.finish_tasks.pack(fill="both", expand=True)
        self.finish_total_time_label = ctk.CTkLabel(frame, text="已記錄總時間: 0 小時")
        self.finish_total_time_label.pack(pady=5)
        self.update_finish_tasks()
        ctk.CTkButton(frame, text="標記為完成", command=self.finish_task).pack(pady=5)

    def update_finish_tasks(self):
        unfinished_tasks = [task["name"] for task in self.data["tasks"] if not task.get("completed", False)]
        for widget in self.finish_tasks.winfo_children():
            widget.destroy()
        if self.selected_finish_task_name and self.selected_finish_task_name not in unfinished_tasks:
            self.selected_finish_task_name = None
        self.finish_task_var = ctk.StringVar(value=self.selected_finish_task_name or "")
        if not unfinished_tasks:
            ctk.CTkLabel(self.finish_tasks, text="沒有未完成的任務").pack(pady=10)
        else:
            for task_name in unfinished_tasks:
                radio = ctk.CTkRadioButton(
                    self.finish_tasks, text=task_name, variable=self.finish_task_var, value=task_name,
                    command=lambda name=task_name: self.select_finish_task(name),
                    fg_color="#4a6cd4", hover_color="#3a5cbd", border_color="#d1d1d1"
                )
                radio.pack(pady=2)
        self.finish_tasks.update_idletasks()
        if self.selected_finish_task_name:
            self.select_finish_task(self.selected_finish_task_name)
        else:
            self.finish_total_time_label.configure(text="已記錄總時間: 0 小時")

    def select_finish_task(self, name):
        self.selected_finish_task_name = name
        self.finish_task_var.set(name)
        for task in self.data["tasks"]:
            if task["name"] == name:
                total_time = sum(segment["hours"] for segment in task["time_segments"])
                self.finish_total_time_label.configure(text=f"已記錄總時間: {total_time:.2f} 小時")
                break

    def finish_task(self):
        if not self.selected_finish_task_name:
            messagebox.showerror("錯誤", "請選擇一個任務！")
            return
        for task in self.data["tasks"]:
            if task["name"] == self.selected_finish_task_name:
                if not task["time_segments"]:
                    if not messagebox.askyesno("警告", "此任務沒有記錄工作時間。確定要標記為完成嗎？"):
                        return
                task["actual_hours"] = sum(segment["hours"] for segment in task["time_segments"]) if task["time_segments"] else 0
                task["end_time"] = datetime.now().isoformat()
                task["completed"] = True
                update_velocity(self.data)
                save_data(self.data)
                messagebox.showinfo("成功", f"任務 '{self.selected_finish_task_name}' 已標記為完成")
                self.selected_finish_task_name = None
                self.update_finish_tasks()
                self.update_record_tasks()
                break

    ### Modify Task Tab ###
    def create_modify_tab(self):
        frame = ctk.CTkScrollableFrame(self.notebook.tab("修改任務"), width=TAB_FRAME_WIDTH, height=TAB_FRAME_HEIGHT)
        frame.pack(pady=5, padx=5, fill="both", expand=True)
        ctk.CTkLabel(frame, text="搜尋任務:").pack(pady=5)
        search_container = ctk.CTkFrame(frame)
        search_container.pack(pady=5, fill="x")
        self.task_search_var = ctk.StringVar()
        self.task_search_entry = ctk.CTkEntry(search_container, width=200, textvariable=self.task_search_var)
        self.task_search_entry.pack(pady=5)
        self.task_search_var.trace_add("write", self.filter_tasks)
        self.task_listbox_frame = ctk.CTkFrame(search_container)
        self.task_listbox_frame.pack(pady=5, fill="x")
        self.task_list_frame = ctk.CTkScrollableFrame(self.task_listbox_frame, width=200, height=150)
        self.task_list_frame.pack(pady=5, fill="both")
        self.update_task_listbox()
        self.modify_task_name = ctk.StringVar()
        ctk.CTkLabel(frame, text="新任務名稱:").pack(pady=5)
        self.new_task_name = ctk.CTkEntry(frame, width=200)
        self.new_task_name.pack(pady=5)
        ctk.CTkLabel(frame, text="新估計時間 (小時):").pack(pady=5)
        self.new_estimated_hours = ctk.CTkEntry(frame, width=100)
        self.new_estimated_hours.pack(pady=5)
        ctk.CTkLabel(frame, text="已記錄時間段:").pack(pady=5)
        self.modify_segments_frame = ctk.CTkScrollableFrame(frame, width=TAB_FRAME_WIDTH, height=80)
        self.modify_segments_frame.pack(pady=5, padx=5)
        ctk.CTkButton(frame, text="刪除選定任務", command=self.delete_task, fg_color="#d12a2a").pack(pady=5)
        ctk.CTkButton(frame, text="修改任務", command=self.modify_task).pack(pady=5)

    def update_task_listbox(self):
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        task_names = [task["name"] for task in self.data["tasks"]]
        for name in task_names:
            btn = ctk.CTkButton(
                self.task_list_frame, text=name, anchor="w", fg_color="transparent",
                text_color=("black", "white"), hover_color=("gray75", "gray25"), height=25,
                command=lambda n=name: self.select_task(n)
            )
            btn.pack(fill="x", pady=1)

    def filter_tasks(self, *args):
        search_text = self.task_search_var.get().lower()
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        for task in self.data["tasks"]:
            name = task["name"]
            if search_text in name.lower():
                btn = ctk.CTkButton(
                    self.task_list_frame, text=name, anchor="w", fg_color="transparent",
                    text_color=("black", "white"), hover_color=("gray75", "gray25"), height=25,
                    command=lambda n=name: self.select_task(n)
                )
                btn.pack(fill="x", pady=1)

    def select_task(self, name):
        self.modify_task_name.set(name)
        self.task_search_var.set("")
        self.update_modify_fields()

    def update_modify_fields(self, event=None):
        name = self.modify_task_name.get()
        for widget in self.modify_segments_frame.winfo_children():
            widget.destroy()
        for task in self.data["tasks"]:
            if task["name"] == name:
                self.new_task_name.delete(0, ctk.END)
                self.new_task_name.insert(0, task["name"])
                self.new_estimated_hours.delete(0, ctk.END)
                self.new_estimated_hours.insert(0, str(task["estimated_hours"]))
                total_time = sum(segment["hours"] for segment in task["time_segments"])
                if task["time_segments"]:
                    ctk.CTkLabel(self.modify_segments_frame, text=f"總計時間: {total_time:.2f} 小時").pack(pady=2)
                for i, segment in enumerate(task["time_segments"]):
                    segment_frame = ctk.CTkFrame(self.modify_segments_frame)
                    segment_frame.pack(fill="x", pady=1)
                    time_str = datetime.fromisoformat(segment["timestamp"]).strftime("%Y-%m-%d %H:%M")
                    label = ctk.CTkLabel(segment_frame, text=f"{segment['hours']:.2f} 小時 ({time_str})")
                    label.pack(side="left", padx=5)
                    delete_btn = ctk.CTkButton(
                        segment_frame, text="X", width=30, height=20, fg_color="#d12a2a",
                        command=lambda t=task["name"], idx=i: self.delete_time_segment(t, idx)
                    )
                    delete_btn.pack(side="right", padx=5)
                break

    def delete_time_segment(self, task_name, segment_index):
        for task in self.data["tasks"]:
            if task["name"] == task_name:
                if messagebox.askyesno("確認", f"確定要刪除時間段 {segment_index+1}？"):
                    if 0 <= segment_index < len(task["time_segments"]):
                        del task["time_segments"][segment_index]
                        task["actual_hours"] = sum(segment["hours"] for segment in task["time_segments"]) if task["time_segments"] else None
                        if task["time_segments"]:
                            task["end_time"] = datetime.now().isoformat()
                        update_velocity(self.data)
                        save_data(self.data)
                        messagebox.showinfo("成功", "時間段已刪除")
                        self.update_modify_fields()
                break

    def delete_task(self):
        name = self.modify_task_name.get()
        if not name:
            messagebox.showerror("錯誤", "請選擇要刪除的任務！")
            return
        if messagebox.askyesno("確認", f"確定要刪除任務 '{name}'？此操作不可恢復。"):
            for i, task in enumerate(self.data["tasks"]):
                if task["name"] == name:
                    del self.data["tasks"][i]
                    save_data(self.data)
                    self.update_task_listbox()
                    self.update_finish_tasks()
                    self.update_record_tasks()
                    self.new_task_name.delete(0, ctk.END)
                    self.new_estimated_hours.delete(0, ctk.END)
                    for widget in self.modify_segments_frame.winfo_children():
                        widget.destroy()
                    messagebox.showinfo("成功", f"任務 '{name}' 已刪除")
                    break

    def modify_task(self):
        old_name = self.modify_task_name.get().strip()
        new_name = self.new_task_name.get().strip()
        try:
            new_estimated = float(self.new_estimated_hours.get()) if self.new_estimated_hours.get().strip() else None
            if not old_name:
                messagebox.showerror("錯誤", "請選擇要修改的任務！")
                return
            task_found = False
            for task in self.data["tasks"]:
                if task["name"] == old_name:
                    task_found = True
                    if new_name and new_name != old_name:
                        # Check for duplicate task name
                        if any(t["name"] == new_name for t in self.data["tasks"] if t["name"] != old_name):
                            messagebox.showerror("錯誤", "新任務名稱已存在！")
                            return
                        task["name"] = new_name
                    if new_estimated is not None and new_estimated > 0:
                        task["estimated_hours"] = new_estimated
                    task["actual_hours"] = sum(segment["hours"] for segment in task["time_segments"]) if task["time_segments"] else None
                    update_velocity(self.data)
                    break
            if not task_found:
                messagebox.showerror("錯誤", "任務未找到！")
                return
            save_data(self.data)
            self.update_task_listbox()
            self.update_finish_tasks()
            self.update_record_tasks()
            messagebox.showinfo("成功", f"任務 '{old_name}' 修改成功！")
        except ValueError:
            messagebox.showerror("錯誤", "時間必須是數字，且大於 0！")

    ### Predict Time Tab ###
    def create_predict_tab(self):
        frame = ctk.CTkScrollableFrame(self.notebook.tab("預測時間"), width=TAB_FRAME_WIDTH, height=TAB_FRAME_HEIGHT)
        frame.pack(pady=5, padx=5, fill="both", expand=True)
        ctk.CTkLabel(frame, text="預測總估計時間 (小時):").pack(pady=5)
        self.predict_hours = ctk.CTkEntry(frame, width=100)
        self.predict_hours.pack(pady=5)
        ctk.CTkButton(frame, text="預測完成時間", command=self.predict_time).pack(pady=5)

    def predict_time(self):
        try:
            hours = float(self.predict_hours.get())
            if hours <= 0:
                messagebox.showerror("錯誤", "預測時間必須大於0！")
                return
            velocity = self.data["velocity"]
            predicted_hours = hours / velocity
            messagebox.showinfo("預測", f"預計完成時間: {predicted_hours:.2f} 小時")
        except ValueError:
            messagebox.showerror("錯誤", "預測時間必須是數字！")

    ### Analyze Tab ###
    def create_analyze_tab(self):
        frame = ctk.CTkScrollableFrame(self.notebook.tab("數據分析"), width=TAB_FRAME_WIDTH, height=TAB_FRAME_HEIGHT)
        frame.pack(pady=5, padx=5, fill="both", expand=True)
        ctk.CTkButton(frame, text="顯示分析", command=self.show_analysis).pack(pady=10)

    def show_analysis(self):
        avg_velocity, completion_rate, estimated, actual, errors = analyze_data(self.data)
        analyze_window = ctk.CTkToplevel(self.root)
        analyze_window.title("數據分析")
        analyze_window.geometry("800x500")
        text = ctk.CTkTextbox(analyze_window, height=100, width=500)
        text.pack(pady=10)
        text.insert("1.0", f"平均速度: {avg_velocity:.2f}\n")
        text.insert("end", f"任務完成率: {completion_rate:.2f}%\n")
        text.insert("end", f"任務數: {len(self.data['tasks'])} (已完成: {len([t for t in self.data['tasks'] if t.get('completed', False)])} 未完成: {len([t for t in self.data['tasks'] if not t.get('completed', False)])})\n")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        ax1.bar(range(len(errors)), errors)
        ax1.set_title("估計 vs 實際誤差 (%)")
        ax1.set_xlabel("任務")
        ax1.set_ylabel("誤差百分比")
        ax1.grid(True)
        velocities = [t["estimated_hours"] / sum(segment["hours"] for segment in t["time_segments"]) 
                      for t in self.data["tasks"] if t.get("completed", False) and t["time_segments"]]
        if velocities:
            ax2.plot(range(len(velocities)), velocities, marker='o')
            ax2.set_title("速度趨勢")
            ax2.set_xlabel("完成任務順序")
            ax2.set_ylabel("速度")
            ax2.grid(True)
        canvas = FigureCanvasTkAgg(fig, master=analyze_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=1)
        plt.close(fig)

if __name__ == "__main__":
    root = ctk.CTk()
    app = EBSSystem(root)
    root.mainloop()