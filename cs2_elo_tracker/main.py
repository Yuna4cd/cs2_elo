import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from pathlib import Path
from typing import List, Dict

from .utils import (
    DATA_DIR, ensure_data_dir, load_json, save_json, 
    load_jsonl, load_aliases, get_display_width, pad_string
)
from .parser import parse_and_save
from .elo import calculate_elos
from .balancer import get_balanced_teams, load_elos

class CS2EloTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("CS2 ELO Tracker")
        self.root.geometry("900x700")
        
        ensure_data_dir()
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_parse_tab()
        self.create_elo_tab()
        self.create_balance_tab()
        self.create_aliases_tab()
        self.create_settings_tab()
        
        # Load initial data
        self.refresh_elos()
        self.refresh_aliases()
    
    def create_parse_tab(self):
        """Tab for parsing match history"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Parse Matches")
        
        # File selection
        file_frame = ttk.LabelFrame(frame, text="Input File")
        file_frame.pack(fill='x', padx=10, pady=10)
        
        self.parse_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.parse_file_var, width=60).pack(side='left', padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_parse_file).pack(side='left', padx=5)
        ttk.Button(file_frame, text="Parse", command=self.parse_file).pack(side='left', padx=5)
        
        # Or paste text
        paste_frame = ttk.LabelFrame(frame, text="Or Paste Match History Text")
        paste_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.paste_text = scrolledtext.ScrolledText(paste_frame, height=15)
        self.paste_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        ttk.Button(paste_frame, text="Parse Pasted Text", command=self.parse_pasted).pack(pady=5)
        
        # Status
        self.parse_status = ttk.Label(frame, text="")
        self.parse_status.pack(pady=10)
    
    def create_elo_tab(self):
        """Tab for viewing ELO rankings"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="ELO Rankings")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Recalculate ELOs", command=self.recalculate_elos).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_elos).pack(side='left', padx=5)
        
        # Filter
        ttk.Label(btn_frame, text="Min Games:").pack(side='left', padx=(20, 5))
        self.min_games_var = tk.StringVar(value="1")
        ttk.Entry(btn_frame, textvariable=self.min_games_var, width=5).pack(side='left')
        ttk.Button(btn_frame, text="Apply", command=self.refresh_elos).pack(side='left', padx=5)
        
        # Treeview for rankings
        columns = ('rank', 'name', 'elo', 'change', 'games', 'wins', 'losses', 'winrate')
        self.elo_tree = ttk.Treeview(frame, columns=columns, show='headings', height=25)
        
        self.elo_tree.heading('rank', text='#')
        self.elo_tree.heading('name', text='Player')
        self.elo_tree.heading('elo', text='ELO')
        self.elo_tree.heading('change', text='Change')
        self.elo_tree.heading('games', text='Games')
        self.elo_tree.heading('wins', text='Wins')
        self.elo_tree.heading('losses', text='Losses')
        self.elo_tree.heading('winrate', text='Win %')
        
        self.elo_tree.column('rank', width=40)
        self.elo_tree.column('name', width=200)
        self.elo_tree.column('elo', width=80)
        self.elo_tree.column('change', width=80)
        self.elo_tree.column('games', width=60)
        self.elo_tree.column('wins', width=60)
        self.elo_tree.column('losses', width=60)
        self.elo_tree.column('winrate', width=60)
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.elo_tree.yview)
        self.elo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.elo_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
    
    def create_balance_tab(self):
        """Tab for team balancing"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Balance Teams")
        
        # Player selection
        select_frame = ttk.LabelFrame(frame, text="Select 10 Players (comma-separated or one per line)")
        select_frame.pack(fill='x', padx=10, pady=10)
        
        self.player_input = scrolledtext.ScrolledText(select_frame, height=5)
        self.player_input.pack(fill='x', padx=5, pady=5)
        
        # Quick select from known players
        quick_frame = ttk.Frame(select_frame)
        quick_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(quick_frame, text="Quick add:").pack(side='left')
        self.quick_player_var = tk.StringVar()
        self.quick_player_combo = ttk.Combobox(quick_frame, textvariable=self.quick_player_var, width=30)
        self.quick_player_combo.pack(side='left', padx=5)
        ttk.Button(quick_frame, text="Add", command=self.add_player).pack(side='left')
        ttk.Button(quick_frame, text="Clear", command=self.clear_players).pack(side='left', padx=5)
        
        ttk.Button(select_frame, text="Balance Teams", command=self.balance_teams).pack(pady=5)
        
        # Hide ELO checkbox
        self.hide_elo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(select_frame, text="Hide individual ELOs", variable=self.hide_elo_var).pack()
        
        # Results
        result_frame = ttk.LabelFrame(frame, text="Balanced Teams")
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.balance_result = scrolledtext.ScrolledText(result_frame, height=20, font=('Courier', 10))
        self.balance_result.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_aliases_tab(self):
        """Tab for managing aliases"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Player Aliases")
        
        # Instructions
        ttk.Label(frame, text="Format: alias -> canonical_name (one per line)").pack(pady=5)
        
        # Text editor for aliases
        self.alias_text = scrolledtext.ScrolledText(frame, height=25, font=('Courier', 10))
        self.alias_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Save Aliases", command=self.save_aliases).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Reload", command=self.refresh_aliases).pack(side='left', padx=5)
    
    def create_settings_tab(self):
        """Tab for settings"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Settings")
        
        # K-Factor
        kf_frame = ttk.Frame(frame)
        kf_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(kf_frame, text="K-Factor:").pack(side='left')
        self.k_factor_var = tk.StringVar(value="32")
        ttk.Entry(kf_frame, textvariable=self.k_factor_var, width=10).pack(side='left', padx=5)
        ttk.Label(kf_frame, text="(Higher = more volatile ratings, 16-50 recommended)").pack(side='left')
        
        # Default ELO
        def_frame = ttk.Frame(frame)
        def_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(def_frame, text="Default ELO:").pack(side='left')
        self.default_elo_var = tk.StringVar(value="1000")
        ttk.Entry(def_frame, textvariable=self.default_elo_var, width=10).pack(side='left', padx=5)
        
        # Data directory info
        dir_frame = ttk.LabelFrame(frame, text="Data Directory")
        dir_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(dir_frame, text=str(DATA_DIR)).pack(padx=5, pady=5)
        ttk.Button(dir_frame, text="Open Folder", command=self.open_data_folder).pack(pady=5)
        
        # Initial ELOs editor
        init_frame = ttk.LabelFrame(frame, text="Initial ELOs (JSON format)")
        init_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.initial_elo_text = scrolledtext.ScrolledText(init_frame, height=15, font=('Courier', 10))
        self.initial_elo_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Load initial ELOs
        init_elos = load_json(DATA_DIR / "initial_elos.json", {})
        self.initial_elo_text.insert('1.0', json.dumps(init_elos, indent=2, ensure_ascii=False))
        
        ttk.Button(init_frame, text="Save Initial ELOs", command=self.save_initial_elos).pack(pady=5)
    
    # === Action methods ===
    
    def browse_parse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Match History File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.parse_file_var.set(filename)
    
    def parse_file(self):
        filepath = self.parse_file_var.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        try:
            total, new, all_matches = parse_and_save(filepath)
            self.parse_status.config(
                text=f"Parsed {total} matches, {new} new. Total in database: {all_matches}"
            )
            self.recalculate_elos()
            messagebox.showinfo("Success", f"Added {new} new matches!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def parse_pasted(self):
        content = self.paste_text.get('1.0', 'end')
        if not content.strip():
            messagebox.showerror("Error", "Please paste match history text first")
            return
        
        try:
            # Save to temp file and parse
            temp_file = DATA_DIR / "temp_paste.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            total, new, all_matches = parse_and_save(str(temp_file))
            temp_file.unlink()  # Delete temp file
            
            self.parse_status.config(
                text=f"Parsed {total} matches, {new} new. Total in database: {all_matches}"
            )
            self.recalculate_elos()
            self.paste_text.delete('1.0', 'end')
            messagebox.showinfo("Success", f"Added {new} new matches!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def recalculate_elos(self):
        try:
            k_factor = int(self.k_factor_var.get())
            calculate_elos(k_factor=k_factor)
            self.refresh_elos()
            messagebox.showinfo("Success", "ELOs recalculated!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def refresh_elos(self):
        # Clear tree
        for item in self.elo_tree.get_children():
            self.elo_tree.delete(item)
        
        # Load and display
        elos = load_json(DATA_DIR / "player_elos.json", [])
        
        try:
            min_games = int(self.min_games_var.get())
        except:
            min_games = 1
        
        for i, player in enumerate(elos, 1):
            if player['games'] >= min_games:
                change = player['elo_change']
                change_str = f"+{change:.0f}" if change >= 0 else f"{change:.0f}"
                
                self.elo_tree.insert('', 'end', values=(
                    i,
                    player['name'],
                    f"{player['elo']:.0f}",
                    change_str,
                    player['games'],
                    player['wins'],
                    player['losses'],
                    f"{player['win_rate']:.1f}%"
                ))
        
        # Update quick player list
        player_names = [p['name'] for p in elos if p['games'] >= min_games]
        self.quick_player_combo['values'] = player_names
    
    def add_player(self):
        player = self.quick_player_var.get()
        if player:
            current = self.player_input.get('1.0', 'end').strip()
            if current:
                self.player_input.insert('end', f"\n{player}")
            else:
                self.player_input.insert('end', player)
            self.quick_player_var.set('')
    
    def clear_players(self):
        self.player_input.delete('1.0', 'end')
    
    def balance_teams(self):
        text = self.player_input.get('1.0', 'end').strip()
        
        # Parse player names (comma or newline separated)
        players = []
        for line in text.replace(',', '\n').split('\n'):
            name = line.strip()
            if name:
                players.append(name)
        
        if len(players) != 10:
            messagebox.showerror("Error", f"Need exactly 10 players, got {len(players)}")
            return
        
        try:
            results = get_balanced_teams(players, num_results=5)
            
            # Display results
            self.balance_result.delete('1.0', 'end')
            hide_elo = self.hide_elo_var.get()
            
            for config in results:
                self.balance_result.insert('end', f"\n{'='*70}\n")
                self.balance_result.insert('end', f"Configuration #{config['rank']} - ELO Difference: {config['elo_difference']:.2f}\n")
                self.balance_result.insert('end', f"{'='*70}\n\n")
                
                self.balance_result.insert('end', f"{'TEAM 1':<30} {'TEAM 2':<30}\n")
                self.balance_result.insert('end', f"Avg ELO: {config['team1_avg_elo']:<20} Avg ELO: {config['team2_avg_elo']}\n")
                self.balance_result.insert('end', f"{'-'*70}\n")
                
                for j in range(5):
                    p1 = config['team1'][j]
                    p2 = config['team2'][j]
                    
                    if hide_elo:
                        self.balance_result.insert('end', f"{p1:<30} {p2:<30}\n")
                    else:
                        e1 = config['team1_elos'][p1]
                        e2 = config['team2_elos'][p2]
                        self.balance_result.insert('end', f"{p1:<20} ({e1:<6.0f})   {p2:<20} ({e2:<6.0f})\n")
                
                self.balance_result.insert('end', "\n")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def refresh_aliases(self):
        aliases = load_aliases()
        
        # Convert to readable format
        lines = []
        for alias, canonical in sorted(aliases.items()):
            if alias != canonical:  # Only show actual aliases
                lines.append(f"{alias} -> {canonical}")
        
        self.alias_text.delete('1.0', 'end')
        self.alias_text.insert('1.0', '\n'.join(lines))
    
    def save_aliases(self):
        text = self.alias_text.get('1.0', 'end')
        
        aliases = {}
        for line in text.split('\n'):
            line = line.strip()
            if '->' in line:
                parts = line.split('->')
                if len(parts) == 2:
                    alias = parts[0].strip()
                    canonical = parts[1].strip()
                    if alias and canonical:
                        aliases[alias] = canonical
        
        save_json(DATA_DIR / "player_aliases.json", aliases)
        messagebox.showinfo("Success", f"Saved {len(aliases)} aliases")
    
    def save_initial_elos(self):
        try:
            text = self.initial_elo_text.get('1.0', 'end')
            data = json.loads(text)
            save_json(DATA_DIR / "initial_elos.json", data)
            messagebox.showinfo("Success", "Initial ELOs saved!")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON: {e}")
    
    def open_data_folder(self):
        import subprocess
        import sys
        
        if sys.platform == 'win32':
            subprocess.run(['explorer', str(DATA_DIR)])
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(DATA_DIR)])
        else:
            subprocess.run(['xdg-open', str(DATA_DIR)])

def main():
    root = tk.Tk()
    app = CS2EloTracker(root)
    root.mainloop()

if __name__ == '__main__':
    main()