import random
import tkinter as tk
from tkinter import messagebox, ttk
from ai import AIHelper

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_mine = False
        self.adjacent_mines = 0
        self.is_revealed = False
        self.is_flagged = False
        self.button = None

class Minesweeper:
    def __init__(self, master):
        self.master = master
        self.master.title("Minesweeper")
        self.master.configure(bg='gray')
        
        # Инициализация ИИ
        self.ai = AIHelper()
        
        # Настройки сложности
        self.difficulties = {
            "Легкий": (9, 9, 10),
            "Средний": (16, 16, 40),
            "Сложный": (16, 30, 99)
        }
        
        # Создаем верхнюю панель
        self.top_frame = tk.Frame(self.master, bg='gray')
        self.top_frame.pack(padx=10, pady=5)
        
        # Выпадающий список сложности
        self.difficulty_var = tk.StringVar(value="Легкий")
        self.difficulty_menu = ttk.Combobox(
            self.top_frame,
            textvariable=self.difficulty_var,
            values=list(self.difficulties.keys()),
            state="readonly",
            width=10
        )
        self.difficulty_menu.pack(side=tk.LEFT, padx=5)
        
        # Кнопка перезапуска
        self.restart_button = tk.Button(
            self.top_frame,
            text="🔄",
            font=('Arial', 12),
            command=self.restart_game
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка помощи ИИ
        self.ai_button = tk.Button(
            self.top_frame,
            text="🤖",
            font=('Arial', 12),
            command=self.get_ai_help
        )
        self.ai_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка статистики ИИ
        self.stats_button = tk.Button(
            self.top_frame,
            text="📊",
            font=('Arial', 12),
            command=self.show_ai_stats
        )
        self.stats_button.pack(side=tk.LEFT, padx=5)
        
        # Счетчик мин
        self.mines_label = tk.Label(
            self.top_frame,
            text="💣: 0",
            font=('Arial', 12, 'bold'),
            bg='gray'
        )
        self.mines_label.pack(side=tk.LEFT, padx=5)
        
        # Фрейм для игрового поля
        self.button_frame = tk.Frame(self.master, bg='gray')
        self.button_frame.pack(padx=10, pady=5)
        
        self.start_new_game()
        
    def start_new_game(self):
        # Очищаем старое игровое поле
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Получаем настройки сложности
        difficulty = self.difficulties[self.difficulty_var.get()]
        self.rows, self.cols, self.mines = difficulty
        
        # Инициализация игровых переменных
        self.cells = [[Cell(x, y) for y in range(self.cols)] for x in range(self.rows)]
        self.mine_positions = set()
        self.game_over = False
        self.first_click = True
        self.flagged_cells = 0
        
        # Обновляем поле для ИИ
        self.ai.set_field(self.cells, self.rows, self.cols)
        
        # Обновляем счетчик мин
        self.update_mines_counter()
        
        # Создаем новое игровое поле
        self.create_board()
        
    def get_ai_help(self):
        if self.game_over or self.first_click:
            print("Игра не началась или закончилась")
            return
            
        # Обновляем состояние ИИ перед каждым ходом
        self.ai.set_field(self.cells, self.rows, self.cols)
        print("Состояние ИИ обновлено")
            
        # Сначала ищем мину
        mine_move = self.ai.get_mine_move()
        print(f"Поиск мины: {mine_move}")
        if mine_move:
            x, y = mine_move
            print(f"Найдена мина в позиции ({x}, {y})")
            if not self.cells[x][y].is_revealed and not self.cells[x][y].is_flagged:
                print("Ставим флажок")
                self.ai.learn_from_move(x, y, True)
                self.toggle_flag(x, y)
                return
            
        # Если не нашли мину, делаем ход
        print("Ищем ход")
        move = self.ai.get_safe_move()  # Этот метод теперь всегда возвращает ход
        print(f"Найден ход: {move}")
        x, y = move
        print(f"Проверяем клетку ({x}, {y})")
        if not self.cells[x][y].is_revealed and not self.cells[x][y].is_flagged:
            print("Делаем ход")
            self.ai.learn_from_move(x, y, True)
            self.handle_click(x, y)
        else:
            print("Клетка уже открыта или помечена флажком")

    def restart_game(self):
        self.start_new_game()
        
    def update_mines_counter(self):
        remaining_mines = self.mines - self.flagged_cells
        self.mines_label.config(text=f"💣: {remaining_mines}")
        
    def create_board(self):
        for x in range(self.rows):
            for y in range(self.cols):
                cell = self.cells[x][y]
                button = tk.Button(
                    self.button_frame,
                    width=3,
                    height=2,
                    font=('Arial', 12, 'bold'),
                    bg='lightgray',
                    relief=tk.RAISED,
                    command=lambda x=x, y=y: self.handle_click(x, y)
                )
                button.bind('<Button-3>', lambda e, x=x, y=y: self.toggle_flag(x, y))
                button.grid(row=x, column=y, padx=1, pady=1)
                cell.button = button

    def place_mines(self, first_x, first_y):
        while len(self.mine_positions) < self.mines:
            x = random.randint(0, self.rows - 1)
            y = random.randint(0, self.cols - 1)
            if (x, y) not in self.mine_positions and \
               (abs(x - first_x) > 1 or abs(y - first_y) > 1):
                self.cells[x][y].is_mine = True
                self.mine_positions.add((x, y))
        self.calculate_adjacent_mines()

    def calculate_adjacent_mines(self):
        for x in range(self.rows):
            for y in range(self.cols):
                if self.cells[x][y].is_mine:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.rows and 0 <= ny < self.cols:
                            if self.cells[nx][ny].is_mine:
                                count += 1
                self.cells[x][y].adjacent_mines = count

    def handle_click(self, x, y):
        if self.game_over or self.cells[x][y].is_flagged:
            return

        if self.first_click:
            self.first_click = False
            self.place_mines(x, y)
            # Обновляем состояние ИИ после размещения мин
            self.ai.set_field(self.cells, self.rows, self.cols)

        if self.cells[x][y].is_mine:
            self.game_over = True
            self.reveal_all_mines()
            # Запоминаем неуспешный ход
            self.ai.learn_from_move(x, y, False)
            messagebox.showinfo("Game Over", "You hit a mine!")
            return

        self.reveal_cell(x, y)
        # Обновляем состояние ИИ после каждого хода
        self.ai.set_field(self.cells, self.rows, self.cols)
        
        if self.check_win():
            messagebox.showinfo("Congratulations", "You won!")

    def reveal_cell(self, x, y):
        cell = self.cells[x][y]
        if cell.is_revealed or cell.is_flagged:
            return

        cell.is_revealed = True
        if cell.is_mine:
            cell.button.config(text="💣", bg="red", relief=tk.SUNKEN)
        else:
            if cell.adjacent_mines > 0:
                cell.button.config(text=str(cell.adjacent_mines), bg="white", relief=tk.SUNKEN)
            else:
                cell.button.config(text="", bg="white", relief=tk.SUNKEN)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.rows and 0 <= ny < self.cols:
                            self.reveal_cell(nx, ny)

    def toggle_flag(self, x, y):
        if self.game_over or self.cells[x][y].is_revealed:
            return

        cell = self.cells[x][y]
        cell.is_flagged = not cell.is_flagged
        
        # Обновляем счетчик флажков
        if cell.is_flagged:
            self.flagged_cells += 1
        else:
            self.flagged_cells -= 1
            
        self.update_mines_counter()
        cell.button.config(text="🚩" if cell.is_flagged else "", bg="lightgray")
        
        # Обновляем состояние ИИ после установки флажка
        self.ai.set_field(self.cells, self.rows, self.cols)

    def reveal_all_mines(self):
        for x in range(self.rows):
            for y in range(self.cols):
                if self.cells[x][y].is_mine:
                    self.cells[x][y].button.config(text="💣", bg="red", relief=tk.SUNKEN)

    def check_win(self):
        for x in range(self.rows):
            for y in range(self.cols):
                cell = self.cells[x][y]
                if not cell.is_mine and not cell.is_revealed:
                    return False
        return True

    def show_ai_stats(self):
        """Показывает статистику обучения ИИ"""
        stats = self.ai.get_stats()
        messagebox.showinfo("AI Statistics", stats)

if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()