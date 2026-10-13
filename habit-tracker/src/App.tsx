import { type FormEvent, useEffect, useMemo, useState } from "react";
import WebApp from "@twa-dev/sdk";

type Habit = {
  id: string;
  title: string;
  emoji: string;
  completedOn: string | null;
};

const STORAGE_KEY = "habit-tracker.habits.v1";

const DEFAULT_HABITS: Habit[] = [
  { id: "water", title: "Выпить воду", emoji: "💧", completedOn: null },
  {
    id: "reading",
    title: "Прочитать 10 страниц",
    emoji: "📚",
    completedOn: null,
  },
  { id: "exercise", title: "Сделать зарядку", emoji: "🏃", completedOn: null },
  {
    id: "coding",
    title: "Изучить программирование",
    emoji: "💻",
    completedOn: null,
  },
];

function getTodayKey(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isHabit(value: unknown): value is Habit {
  if (typeof value !== "object" || value === null) return false;

  const habit = value as Record<string, unknown>;
  return (
    typeof habit.id === "string" &&
    typeof habit.title === "string" &&
    typeof habit.emoji === "string" &&
    (typeof habit.completedOn === "string" || habit.completedOn === null)
  );
}

function loadHabits(): { habits: Habit[]; error: string | null } {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === null) {
      return { habits: DEFAULT_HABITS, error: null };
    }

    const parsed: unknown = JSON.parse(saved);
    if (!Array.isArray(parsed) || !parsed.every(isHabit)) {
      throw new Error("Saved habits have an invalid format");
    }

    return { habits: parsed, error: null };
  } catch {
    return {
      habits: DEFAULT_HABITS,
      error: "Не удалось прочитать сохранённые привычки. Загружен начальный список.",
    };
  }
}

function applyTelegramTheme(): void {
  const theme = WebApp.themeParams;
  const root = document.documentElement;

  root.dataset.theme = WebApp.colorScheme;
  const themeVariables: Record<string, string | undefined> = {
    "--tg-bg": theme.bg_color,
    "--tg-text": theme.text_color,
    "--tg-hint": theme.hint_color,
    "--tg-secondary-bg": theme.secondary_bg_color,
    "--tg-button": theme.button_color,
    "--tg-button-text": theme.button_text_color,
  };

  for (const [name, value] of Object.entries(themeVariables)) {
    if (value) {
      root.style.setProperty(name, value);
    } else {
      root.style.removeProperty(name);
    }
  }
}

function App() {
  const [initialState] = useState(loadHabits);
  const [habits, setHabits] = useState<Habit[]>(initialState.habits);
  const [storageError, setStorageError] = useState<string | null>(
    initialState.error,
  );
  const [hasPendingChanges, setHasPendingChanges] = useState(false);
  const [newHabitTitle, setNewHabitTitle] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isTelegram, setIsTelegram] = useState(false);
  const today = getTodayKey();

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    applyTelegramTheme();
    setIsTelegram(Boolean(WebApp.initData));
    WebApp.onEvent("themeChanged", applyTelegramTheme);

    return () => {
      WebApp.offEvent("themeChanged", applyTelegramTheme);
    };
  }, []);

  useEffect(() => {
    if (!hasPendingChanges) return;

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(habits));
      setStorageError(null);
    } catch {
      setStorageError(
        "Не удалось сохранить изменения. Проверьте свободное место и настройки браузера.",
      );
    }
    setHasPendingChanges(false);
  }, [habits, hasPendingChanges]);

  const completedCount = useMemo(
    () => habits.filter((habit) => habit.completedOn === today).length,
    [habits, today],
  );
  const progress = habits.length
    ? Math.round((completedCount / habits.length) * 100)
    : 0;

  function toggleHabit(id: string): void {
    setHabits((current) =>
      current.map((habit) =>
        habit.id === id
          ? {
              ...habit,
              completedOn: habit.completedOn === today ? null : today,
            }
          : habit,
      ),
    );
    setHasPendingChanges(true);
  }

  function addHabit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const title = newHabitTitle.trim();

    if (!title) {
      setFormError("Введите название привычки.");
      return;
    }
    if (title.length > 60) {
      setFormError("Название должно быть не длиннее 60 символов.");
      return;
    }
    if (
      habits.some(
        (habit) => habit.title.toLocaleLowerCase() === title.toLocaleLowerCase(),
      )
    ) {
      setFormError("Такая привычка уже есть в списке.");
      return;
    }

    setHabits((current) => [
      ...current,
      {
        id: `custom-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        title,
        emoji: "✨",
        completedOn: null,
      },
    ]);
    setHasPendingChanges(true);
    setNewHabitTitle("");
    setFormError(null);
  }

  const formattedDate = new Intl.DateTimeFormat("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());

  return (
    <main className="app-shell">
      <div className="app-content">
        <header className="page-header">
          <div className="header-copy">
            <p className="eyebrow">ТВОЙ РИТМ, ТВОИ ПРАВИЛА</p>
            <h1>Мои привычки</h1>
            <p className="date-label">{formattedDate}</p>
          </div>
          {isTelegram && (
            <button
              className="close-button"
              type="button"
              aria-label="Закрыть приложение"
              onClick={() => WebApp.close()}
            >
              ×
            </button>
          )}
        </header>

        <section className="progress-card" aria-label="Прогресс за день">
          <div className="progress-heading">
            <div>
              <p className="progress-label">ПРОГРЕСС ЗА ДЕНЬ</p>
              <p className="progress-count">
                <strong>{completedCount}</strong>
                <span> из {habits.length} выполнено</span>
              </p>
            </div>
            <div
              className="progress-ring"
              role="img"
              aria-label={`Выполнено ${progress}%`}
              style={{ "--progress": `${progress}%` } as React.CSSProperties}
            >
              <span>{progress}%</span>
            </div>
          </div>
          <div
            className="progress-track"
            role="progressbar"
            aria-label="Привычки, выполненные сегодня"
            aria-valuemin={0}
            aria-valuemax={Math.max(habits.length, 1)}
            aria-valuenow={completedCount}
          >
            <span style={{ width: `${progress}%` }} />
          </div>
          <p className="progress-caption">
            {habits.length === 0
              ? "Добавь первую привычку — начни свой день!"
              : progress === 100
                ? "Отлично! Все привычки на сегодня выполнены 🎉"
                : "Маленькие шаги каждый день — большой результат."}
          </p>
        </section>

        <section className="habits-section" aria-labelledby="habits-heading">
          <div className="section-heading">
            <div>
              <h2 id="habits-heading">На сегодня</h2>
              <p>Отмечай каждую маленькую победу</p>
            </div>
            <span className="habit-total">{habits.length}</span>
          </div>

          {habits.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon" aria-hidden="true">
                🌱
              </span>
              <h3>Здесь пока пусто</h3>
              <p>Добавь привычку ниже, и она появится в твоём списке.</p>
            </div>
          ) : (
            <ul className="habit-list">
              {habits.map((habit) => {
                const isCompleted = habit.completedOn === today;
                return (
                  <li
                    className={`habit-card${isCompleted ? " is-completed" : ""}`}
                    key={habit.id}
                  >
                    <span className="habit-emoji" aria-hidden="true">
                      {habit.emoji}
                    </span>
                    <span className="habit-title">{habit.title}</span>
                    <button
                      className="complete-button"
                      type="button"
                      aria-label={`${isCompleted ? "Снять отметку" : "Отметить выполнение"}: ${habit.title}`}
                      aria-pressed={isCompleted}
                      onClick={() => toggleHabit(habit.id)}
                    >
                      {isCompleted ? "✓" : ""}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="add-section" aria-labelledby="add-heading">
          <h2 id="add-heading">Новая привычка</h2>
          <form className="add-form" onSubmit={addHabit} noValidate>
            <label className="visually-hidden" htmlFor="habit-title">
              Название привычки
            </label>
            <input
              id="habit-title"
              type="text"
              maxLength={60}
              placeholder="Например, прогуляться 20 минут"
              value={newHabitTitle}
              aria-invalid={Boolean(formError)}
              aria-describedby={formError ? "form-error" : undefined}
              onChange={(event) => {
                setNewHabitTitle(event.target.value);
                setFormError(null);
              }}
            />
            <button type="submit" aria-label="Добавить привычку">
              +
            </button>
          </form>
          {formError && (
            <p className="form-error" id="form-error" role="alert">
              {formError}
            </p>
          )}
          {storageError && (
            <p className="storage-error" role="alert">
              {storageError}
            </p>
          )}
        </section>
        <p className="footer-note">Регулярность важнее идеального результата ✨</p>
      </div>
    </main>
  );
}

export default App;
