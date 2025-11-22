"""
比赛管理图形界面
使用tkinter创建图形界面来选择和管理比赛
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.agent_loader import AgentLoader
from tournament.tournament import RoundRobinTournament, EliminationTournament
from tournament.group_tournament import GroupTournament
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer


class TournamentGUI:
    """比赛管理图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI竞技平台 - 比赛管理系统")
        self.root.geometry("900x700")
        
        self.agents = []
        self.tournament_thread = None
        
        self._create_widgets()
        self._load_agents()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 标题
        title_frame = tk.Frame(self.root)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="AI竞技平台 - 比赛管理系统", 
                font=("Arial", 16, "bold")).pack()
        
        # Agent列表区域
        agent_frame = tk.LabelFrame(self.root, text="参赛者列表", padx=10, pady=10)
        agent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Agent列表
        list_frame = tk.Frame(agent_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.agent_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                        selectmode=tk.EXTENDED, height=10)
        self.agent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.agent_listbox.yview)
        
        # 刷新按钮
        refresh_btn = tk.Button(agent_frame, text="刷新列表", command=self._load_agents)
        refresh_btn.pack(pady=5)
        
        # 比赛设置区域
        settings_frame = tk.LabelFrame(self.root, text="比赛设置", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 比赛模式选择
        mode_frame = tk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        tk.Label(mode_frame, text="比赛模式:").pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="group")
        modes = [
            ("分组赛（适合大规模）", "group"),
            ("循环赛", "round_robin"),
            ("淘汰赛", "elimination"),
            ("组队对战", "team_battle")
        ]
        for text, value in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, 
                          value=value).pack(side=tk.LEFT, padx=5)
        
        # 分组设置（仅分组赛显示）
        self.group_frame = tk.Frame(settings_frame)
        self.group_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(self.group_frame, text="每组人数:").pack(side=tk.LEFT, padx=5)
        self.group_size_var = tk.IntVar(value=4)
        group_size_spin = tk.Spinbox(self.group_frame, from_=2, to=10, 
                                     textvariable=self.group_size_var, width=5)
        group_size_spin.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.group_frame, text="每组出线:").pack(side=tk.LEFT, padx=5)
        self.advance_var = tk.IntVar(value=2)
        advance_spin = tk.Spinbox(self.group_frame, from_=1, to=5, 
                                  textvariable=self.advance_var, width=5)
        advance_spin.pack(side=tk.LEFT, padx=5)
        
        # 组队设置（仅组队对战显示）
        self.team_frame = tk.Frame(settings_frame)
        
        tk.Label(self.team_frame, text="队伍数量:").pack(side=tk.LEFT, padx=5)
        self.num_teams_var = tk.IntVar(value=2)
        num_teams_spin = tk.Spinbox(self.team_frame, from_=2, to=4, 
                                    textvariable=self.num_teams_var, width=5)
        num_teams_spin.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.team_frame, text="(选择Agent后点击'分配队伍'按钮)").pack(side=tk.LEFT, padx=5)
        
        self.assign_teams_btn = tk.Button(self.team_frame, text="分配队伍", 
                                          command=self._assign_teams)
        self.assign_teams_btn.pack(side=tk.LEFT, padx=5)
        
        # 队伍分配显示区域
        self.team_assignment_text = tk.Text(self.team_frame, height=4, width=60, wrap=tk.WORD)
        self.team_assignment_text.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 最大轮次设置
        max_turns_frame = tk.Frame(settings_frame)
        max_turns_frame.pack(fill=tk.X, pady=5)
        tk.Label(max_turns_frame, text="最大轮次:").pack(side=tk.LEFT, padx=5)
        self.max_turns_var = tk.IntVar(value=2000)
        max_turns_spin = tk.Spinbox(max_turns_frame, from_=100, to=10000, 
                                    textvariable=self.max_turns_var, width=8, increment=100)
        max_turns_spin.pack(side=tk.LEFT, padx=5)
        tk.Label(max_turns_frame, text="(回合数，防止无限循环)").pack(side=tk.LEFT, padx=5)
        
        # 开始比赛按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.start_btn = tk.Button(button_frame, text="开始比赛", 
                                   command=self._start_tournament,
                                   bg="#4CAF50", fg="white", 
                                   font=("Arial", 12, "bold"),
                                   width=15, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="停止比赛", 
                                  command=self._stop_tournament,
                                  bg="#f44336", fg="white",
                                  state=tk.DISABLED,
                                  width=15, height=2)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 输出区域
        output_frame = tk.LabelFrame(self.root, text="比赛输出", padx=10, pady=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, 
                                                     wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 绑定模式变化事件
        self.mode_var.trace('w', self._on_mode_change)
    
    def _on_mode_change(self, *args):
        """比赛模式改变时的处理"""
        mode = self.mode_var.get()
        if mode == "group":
            self.group_frame.pack(fill=tk.X, pady=5)
            self.team_frame.pack_forget()
        elif mode == "team_battle":
            self.group_frame.pack_forget()
            self.team_frame.pack(fill=tk.X, pady=5)
        else:
            self.group_frame.pack_forget()
            self.team_frame.pack_forget()
    
    def _assign_teams(self):
        """为选中的Agent分配队伍"""
        selected_indices = self.agent_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请先选择要分配的Agent")
            return
        
        selected_agents = [self.agents[i] for i in selected_indices]
        num_teams = self.num_teams_var.get()
        
        if len(selected_agents) < num_teams:
            messagebox.showwarning("警告", f"至少需要 {num_teams} 个Agent才能分成 {num_teams} 队")
            return
        
        # 平均分配队伍
        import random
        random.shuffle(selected_agents)
        agents_per_team = len(selected_agents) // num_teams
        remainder = len(selected_agents) % num_teams
        
        team_assignments = {}
        idx = 0
        for team_id in range(1, num_teams + 1):
            team_size = agents_per_team + (1 if team_id <= remainder else 0)
            team_agents = selected_agents[idx:idx + team_size]
            for agent in team_agents:
                agent.team_id = team_id
                team_assignments[agent.name] = team_id
            idx += team_size
        
        # 显示分配结果
        self.team_assignment_text.delete(1.0, tk.END)
        for team_id in range(1, num_teams + 1):
            team_members = [name for name, tid in team_assignments.items() if tid == team_id]
            self.team_assignment_text.insert(tk.END, f"队伍 {team_id}: {', '.join(team_members)}\n")
        
        messagebox.showinfo("成功", f"已为 {len(selected_agents)} 个Agent分配到 {num_teams} 个队伍")
    
    def _load_agents(self):
        """加载Agent列表"""
        self.output_text.insert(tk.END, "正在加载参赛者Agent...\n")
        self.root.update()
        
        try:
            loader = AgentLoader(participants_dir="participants")
            self.agents = loader.create_agent_instances()
            
            # 更新列表
            self.agent_listbox.delete(0, tk.END)
            for agent in self.agents:
                self.agent_listbox.insert(tk.END, f"{agent.name} ({agent.__class__.__name__})")
            
            self.output_text.insert(tk.END, f"成功加载 {len(self.agents)} 个Agent\n\n")
        except Exception as e:
            messagebox.showerror("错误", f"加载Agent失败: {e}")
            self.output_text.insert(tk.END, f"加载失败: {e}\n")
        
        self.root.update()
    
    def _log(self, message):
        """输出日志"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
    
    def _start_tournament(self):
        """开始比赛"""
        if len(self.agents) < 2:
            messagebox.showwarning("警告", "至少需要2个Agent才能进行比赛")
            return
        
        # 获取选中的Agent（如果未选中，使用全部）
        selected_indices = self.agent_listbox.curselection()
        if selected_indices:
            selected_agents = [self.agents[i] for i in selected_indices]
        else:
            selected_agents = self.agents
        
        if len(selected_agents) < 2:
            messagebox.showwarning("警告", "至少需要选择2个Agent")
            return
        
        # 禁用开始按钮，启用停止按钮
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 清空输出
        self.output_text.delete(1.0, tk.END)
        
        # 在新线程中运行比赛
        mode = self.mode_var.get()
        self.tournament_thread = threading.Thread(
            target=self._run_tournament,
            args=(selected_agents, mode),
            daemon=True
        )
        self.tournament_thread.start()
    
    def _run_tournament(self, agents, mode):
        """运行比赛（在后台线程中）"""
        try:
            self._log(f"开始比赛，共 {len(agents)} 个Agent")
            self._log(f"比赛模式: {mode}\n")
            
            max_turns = self.max_turns_var.get()
            self._log(f"最大轮次: {max_turns}\n")
            
            if mode == "group":
                group_size = self.group_size_var.get()
                advance = self.advance_var.get()
                self._log(f"分组设置: 每组 {group_size} 人，每组出线 {advance} 人\n")
                
                tournament = GroupTournament(agents, group_size=group_size, 
                                           advance_per_group=advance,
                                           save_replay=True, replay_dir="replays",
                                           max_turns=max_turns)
                result = tournament.run(verbose=False)
                
                # 输出结果
                self._log("\n" + "="*60)
                self._log("比赛完成！")
                self._log("="*60)
                self._log(f"冠军: {result['champion'].name}")
                self._log(f"小组数: {result['groups']}")
                self._log(f"出线人数: {result['advanced']}\n")
                
                tournament.print_results()
                
            elif mode == "round_robin":
                tournament = RoundRobinTournament(agents, save_replay=True, replay_dir="replays",
                                                 max_turns=max_turns)
                tournament.run(verbose=False)
                self._log("\n比赛完成！回放文件已保存到 replays/ 目录")
                tournament.print_results()
                
            elif mode == "elimination":
                tournament = EliminationTournament(agents, save_replay=True, replay_dir="replays",
                                                  max_turns=max_turns)
                champion = tournament.run(verbose=False)
                self._log(f"\n比赛完成！冠军: {champion.name}")
                self._log("回放文件已保存到 replays/ 目录")
                tournament.print_results()
                
            elif mode == "team_battle":
                # 检查是否有队伍分配
                team_agents = [a for a in agents if hasattr(a, 'team_id') and a.team_id is not None]
                if len(team_agents) < 2:
                    self._log("错误: 请先选择Agent并点击'分配队伍'按钮")
                    return
                
                # 显示队伍信息
                teams = {}
                for agent in team_agents:
                    tid = agent.team_id
                    if tid not in teams:
                        teams[tid] = []
                    teams[tid].append(agent.name)
                
                self._log("队伍配置:")
                for tid, members in sorted(teams.items()):
                    self._log(f"  队伍 {tid}: {', '.join(members)}")
                self._log("")
                
                # 运行组队对战
                engine = GameEngine(team_agents, map_width=100, map_height=100)
                visualizer = WebVisualizer(100, 100)
                
                frame_interval = 2
                # 固定跑满 max_turns，再按评分判定队伍胜负
                while engine.state.turn < max_turns:
                    state = engine.step()
                    if engine.state.turn % frame_interval == 0:
                        visualizer.record_frame(state)
                
                # 按队伍评分：存活人数 > 总击杀数 > 总血量
                winning_team = None
                alive = engine.state.get_alive_agents()
                team_scores = {}
                for agent in alive:
                    if getattr(agent, "team_id", None) is None:
                        continue
                    tid = agent.team_id
                    if tid not in team_scores:
                        team_scores[tid] = {"alive": 0, "kills": 0, "health": 0}
                    team_scores[tid]["alive"] += 1
                    team_scores[tid]["kills"] += agent.kills
                    team_scores[tid]["health"] += agent.health
                if team_scores:
                    scored = [
                        (
                            tid,
                            s["alive"] * 1000000 + s["kills"] * 10000 + s["health"],
                        )
                        for tid, s in team_scores.items()
                    ]
                    scored.sort(key=lambda x: x[1], reverse=True)
                    if len(scored) == 1 or scored[0][1] > scored[1][1]:
                        winning_team = scored[0][0]
                
                # 输出结果
                self._log("\n" + "="*60)
                self._log("组队对战完成！")
                self._log("="*60)
                if winning_team:
                    self._log(f"胜利队伍: 队伍 {winning_team}")
                    self._log(f"队伍成员: {', '.join(teams[winning_team])}")
                    # 显示队伍统计
                    alive = engine.state.get_alive_agents()
                    team_alive = [a for a in alive if hasattr(a, 'team_id') and a.team_id == winning_team]
                    team_kills = sum(a.kills for a in team_alive)
                    team_health = sum(a.health for a in team_alive)
                    self._log(f"队伍统计: 存活 {len(team_alive)} 人, 总击杀 {team_kills}, 总血量 {team_health}")
                else:
                    self._log("完全平局，无队伍获胜")
                    alive = engine.state.get_alive_agents()
                    if alive:
                        self._log(f"剩余存活: {len(alive)} 人")
                        # 按队伍分组显示
                        by_team = {}
                        for a in alive:
                            tid = a.team_id if hasattr(a, 'team_id') and a.team_id is not None else '无队伍'
                            if tid not in by_team:
                                by_team[tid] = []
                            by_team[tid].append(a)
                        for tid, members in sorted(by_team.items()):
                            total_kills = sum(a.kills for a in members)
                            total_health = sum(a.health for a in members)
                            self._log(f"  队伍 {tid}: {len(members)} 人, 总击杀 {total_kills}, 总血量 {total_health}")
                            for a in members:
                                self._log(f"    - {a.name}: 击杀={a.kills}, 血量={a.health}")
                
                # 保存回放
                from pathlib import Path
                replay_dir = Path("replays")
                replay_dir.mkdir(exist_ok=True)
                team_names = "_vs_".join([f"Team{tid}" for tid in sorted(teams.keys())])
                replay_file = replay_dir / f"team_battle_{team_names}.html"
                visualizer.generate_html(str(replay_file), auto_play=True, fps=15)
                self._log(f"\n回放文件已保存: {replay_file}")
            
            self._log("\n比赛结束！")
            
        except Exception as e:
            self._log(f"\n错误: {e}")
            import traceback
            self._log(traceback.format_exc())
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
    
    def _stop_tournament(self):
        """停止比赛"""
        # 注意：由于比赛在后台线程运行，这里只能提示
        messagebox.showinfo("提示", "比赛正在运行中，请等待完成")


def main():
    """主函数"""
    root = tk.Tk()
    app = TournamentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

