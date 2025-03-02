import customtkinter as ctk
from tkinter import messagebox
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 設定 matplotlib 字體為中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 用雅黑
plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示

# 數據檔案
DATA_FILE = "ebs_data.json"

# 載入或初始化數據
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"tasks": [], "velocity": 1.0}

# 保存數據
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# 計算速度並更新
def update_velocity(data):
    completed = [t for t in data["tasks"] if t["actual_hours"] is not None]
    if completed:
        total_velocity = sum(t["estimated_hours"] / t["actual_hours"] for t in completed)
        data["velocity"] = total_velocity / len(completed)
    save_data(data)

# 數據分析
def analyze_data(data):
    completed = [t for t in data["tasks"] if t["actual_hours"] is not None]
    unfinished = [t for t in data["tasks"] if t["actual_hours"] is None]
    
    avg_velocity = data["velocity"] if completed else 1.0
    completion_rate = (len(completed) / len(data["tasks"]) * 100) if data["tasks"] else 0.0
    estimated = [t["estimated_hours"] for t in completed]
    actual = [t["actual_hours"] for t in completed]
    errors = [(e - a) / e * 100 if e > 0 else 0 for e, a in zip(estimated, actual)]
    
    return avg_velocity, completion_rate, estimated, actual, errors

# GUI 主窗體
class EBSSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Evidence-Based Scheduling")
        self.root.geometry("600x400")  # 現代化大小，適應螢幕
        self.root.resizable(True, True)  # 允許調整大小

        ctk.set_appearance_mode("dark")  # 深色模式
        ctk.set_default_color_theme("blue")  # 藍色主題

        self.data = load_data()

        # 使用 Notebook 分頁
        self.notebook = ctk.CTkTabview(root, width=580, height=360)
        self.notebook.pack(pady=10, padx=10)

        # 添加分頁
        self.notebook.add("添加任務")
        self.notebook.add("完成任務")
        self.notebook.add("修改任務")
        self.notebook.add("預測時間")
        self.notebook.add("數據分析")

        self.selected_finish_task_name = None  # 用 None 記錄選中任務名

        # 添加任務分頁
        self.create_add_tab()
        # 完成任務分頁
        self.create_finish_tab()
        # 修改任務分頁
        self.create_modify_tab()
        # 預測時間分頁
        self.create_predict_tab()
        # 數據分析分頁
        self.create_analyze_tab()


    def create_add_tab(self):
        frame = self.notebook.tab("添加任務")
        ctk.CTkLabel(frame, text="任務名稱:").pack(pady=5)
        self.task_name = ctk.CTkEntry(frame, width=200)
        self.task_name.pack(pady=5)

        ctk.CTkLabel(frame, text="估計時間 (小時):").pack(pady=5)
        self.estimated_hours = ctk.CTkEntry(frame, width=100)
        self.estimated_hours.pack(pady=5)

        ctk.CTkButton(frame, text="添加任務", command=self.add_task).pack(pady=5)

    def create_finish_tab(self):
        frame = self.notebook.tab("完成任務")
        # 用滾動框顯示未完成任務
        scroll_frame = ctk.CTkScrollableFrame(frame, width=200, height=150)
        scroll_frame.pack(pady=5, padx=5)
        
        self.finish_tasks = ctk.CTkFrame(scroll_frame)  # Frame 放單選按鈕
        self.finish_tasks.pack(fill="both", expand=True)
        
        self.update_finish_tasks()

        ctk.CTkLabel(frame, text="實際時間 (小時):").pack(pady=5)
        self.finish_actual_hours = ctk.CTkEntry(frame, width=100)
        self.finish_actual_hours.pack(pady=5)

        ctk.CTkButton(frame, text="完成任務", command=self.finish_task).pack(pady=5)

    def update_finish_tasks(self):
        unfinished_tasks = [task["name"] for task in self.data["tasks"] if task["actual_hours"] is None]
        for widget in self.finish_tasks.winfo_children():  # 清理舊單選按鈕
            widget.destroy()
        
        # 建立變數來追蹤選中的單選按鈕
        self.finish_task_var = ctk.StringVar(value=self.selected_finish_task_name if self.selected_finish_task_name else "")
        
        for task_name in unfinished_tasks:
            radio = ctk.CTkRadioButton(
                self.finish_tasks, 
                text=task_name, 
                variable=self.finish_task_var,
                value=task_name,
                fg_color="#4a6cd4",      # 選中時的顏色 (中等藍色)
                hover_color="#3a5cbd",   # 懸停時的顏色 (較深藍色)
                border_color="#d1d1d1"   # 邊框顏色 (淺灰色)
            )
            radio.pack(pady=2)
        
        self.finish_tasks.update_idletasks()

    def create_modify_tab(self):
        frame = self.notebook.tab("修改任務")
        ctk.CTkLabel(frame, text="選擇任務名稱:").pack(pady=5)
        self.modify_task_name = ctk.StringVar()
        self.task_list = ctk.CTkComboBox(frame, variable=self.modify_task_name, values=[task["name"] for task in self.data["tasks"]], state="readonly", width=200)
        self.task_list.pack(pady=5)
        self.task_list.bind("<<ComboboxSelected>>", self.update_modify_fields)

        ctk.CTkLabel(frame, text="新任務名稱:").pack(pady=5)
        self.new_task_name = ctk.CTkEntry(frame, width=200)
        self.new_task_name.pack(pady=5)

        ctk.CTkLabel(frame, text="新估計時間 (小時):").pack(pady=5)
        self.new_estimated_hours = ctk.CTkEntry(frame, width=100)
        self.new_estimated_hours.pack(pady=5)

        ctk.CTkLabel(frame, text="新實際時間 (小時):").pack(pady=5)
        self.new_actual_hours = ctk.CTkEntry(frame, width=100)
        self.new_actual_hours.pack(pady=5)

        ctk.CTkButton(frame, text="修改任務", command=self.modify_task).pack(pady=5)

    def create_predict_tab(self):
        frame = self.notebook.tab("預測時間")
        ctk.CTkLabel(frame, text="預測總估計時間 (小時):").pack(pady=5)
        self.predict_hours = ctk.CTkEntry(frame, width=100)
        self.predict_hours.pack(pady=5)

        ctk.CTkButton(frame, text="預測完成時間", command=self.predict_time).pack(pady=5)

    def create_analyze_tab(self):
        frame = self.notebook.tab("數據分析")
        ctk.CTkButton(frame, text="顯示分析", command=self.show_analysis).pack(pady=10)

    def update_task_list(self):
        self.task_list.set("")  # 清空選擇
        self.task_list['values'] = [task["name"] for task in self.data["tasks"]]

    def update_modify_fields(self, event=None):
        name = self.modify_task_name.get()
        for task in self.data["tasks"]:
            if task["name"] == name:
                self.new_task_name.delete(0, ctk.END)
                self.new_task_name.insert(0, task["name"])
                self.new_estimated_hours.delete(0, ctk.END)
                self.new_estimated_hours.insert(0, str(task["estimated_hours"]))
                self.new_actual_hours.delete(0, ctk.END)
                self.new_actual_hours.insert(0, str(task["actual_hours"]) if task["actual_hours"] is not None else "")
                break

    def add_task(self):
        name = self.task_name.get().strip()
        try:
            hours = float(self.estimated_hours.get())
            if name and hours > 0:
                task = {
                    "name": name,
                    "estimated_hours": hours,
                    "actual_hours": None,
                    "start_time": datetime.now().isoformat()
                }
                self.data["tasks"].append(task)
                save_data(self.data)
                self.update_task_list()
                self.update_finish_tasks()  # 刷新完成任務選單
                self.task_name.delete(0, ctk.END)  # 清空任務名稱
                self.estimated_hours.delete(0, ctk.END)  # 清空估計時間
                messagebox.showinfo("成功", f"任務 '{name}' 添加成功！")
            else:
                messagebox.showerror("錯誤", "任務名稱和估計時間必須有效！")
        except ValueError:
            messagebox.showerror("錯誤", "估計時間必須是數字！")

    def finish_task(self):
        if self.selected_finish_task_name:
            name = self.selected_finish_task_name
        else:
            messagebox.showerror("錯誤", "請選擇一個任務！")
            return
        try:
            hours = float(self.finish_actual_hours.get())
            if hours > 0:
                for task in self.data["tasks"]:
                    if task["name"] == name and task["actual_hours"] is None:
                        task["actual_hours"] = hours
                        task["end_time"] = datetime.now().isoformat()
                        update_velocity(self.data)
                        self.update_task_list()
                        self.update_finish_tasks()  # 刷新完成任務選單
                        self.finish_actual_hours.delete(0, ctk.END)  # 清空實際時間
                        messagebox.showinfo("成功", f"任務 '{name}' 完成，速度: {self.data['velocity']:.2f}")
                        return
                messagebox.showerror("錯誤", "任務未找到或已完成！")
            else:
                messagebox.showerror("錯誤", "實際時間必須有效！")
        except ValueError:
            messagebox.showerror("錯誤", "實際時間必須是數字！")

    def predict_time(self):
        try:
            hours = float(self.predict_hours.get())
            if hours > 0:
                velocity = self.data["velocity"]
                predicted_hours = hours / velocity
                messagebox.showinfo("預測", f"預計完成時間: {predicted_hours:.2f} 小時")
            else:
                messagebox.showerror("錯誤", "預測時間必須有效！")
        except ValueError:
            messagebox.showerror("錯誤", "預測時間必須是數字！")

    def modify_task(self):
        name = self.modify_task_name.get().strip()
        new_name = self.new_task_name.get().strip()
        try:
            new_estimated = float(self.new_estimated_hours.get()) if self.new_estimated_hours.get().strip() else None
            new_actual = float(self.new_actual_hours.get()) if self.new_actual_hours.get().strip() else None

            if not name:
                messagebox.showerror("錯誤", "請選擇要修改的任務！")
                return

            task_found = False
            for i, task in enumerate(self.data["tasks"]):
                if task["name"] == name:
                    task_found = True
                    if new_name:
                        task["name"] = new_name
                    if new_estimated is not None and new_estimated > 0:
                        task["estimated_hours"] = new_estimated
                    if new_actual is not None and new_actual >= 0:
                        task["actual_hours"] = new_actual
                        if new_actual > 0:
                            task["end_time"] = datetime.now().isoformat()
                    update_velocity(self.data)
                    break

            if not task_found:
                messagebox.showerror("錯誤", "任務未找到！")
                return

            save_data(self.data)
            self.update_task_list()
            self.update_finish_tasks()  # 刷新完成任務選單
            messagebox.showinfo("成功", f"任務 '{name}' 修改成功！")
        except ValueError:
            messagebox.showerror("錯誤", "時間必須是數字，且大於 0！")

    def show_analysis(self):
        avg_velocity, completion_rate, estimated, actual, errors = analyze_data(self.data)

        # 創建分析視窗
        analyze_window = ctk.CTkToplevel(self.root)
        analyze_window.title("數據分析")
        analyze_window.geometry("800x500")

        # 文字顯示
        text = ctk.CTkTextbox(analyze_window, height=100, width=500)
        text.pack(pady=10)
        text.insert("1.0", f"平均速度: {avg_velocity:.2f}\n")
        text.insert("end", f"任務完成率: {completion_rate:.2f}%\n")
        text.insert("end", f"任務數: {len(self.data['tasks'])} (已完成: {len([t for t in self.data['tasks'] if t['actual_hours'] is not None])}, 未完成: {len([t for t in self.data['tasks'] if t['actual_hours'] is None])})")

        # 畫圖 - 估計 vs 實際誤差
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # 誤差柱狀圖
        ax1.bar(range(len(errors)), errors)
        ax1.set_title("估計 vs 實際誤差 (%)")
        ax1.set_xlabel("任務")
        ax1.set_ylabel("誤差百分比")
        ax1.grid(True)

        # 速度趨勢
        velocities = []
        for task in self.data["tasks"]:
            if task["actual_hours"] is not None:
                velocities.append(task["estimated_hours"] / task["actual_hours"])
        if velocities:
            ax2.plot(range(len(velocities)), velocities, marker='o')
            ax2.set_title("速度趨勢")
            ax2.set_xlabel("完成任務順序")
            ax2.set_ylabel("速度")
            ax2.grid(True)

        # 嵌入圖表到 customtkinter
        canvas = FigureCanvasTkAgg(fig, master=analyze_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=1)

        plt.close(fig)

if __name__ == "__main__":
    root = ctk.CTk()
    app = EBSSystem(root)
    root.mainloop()