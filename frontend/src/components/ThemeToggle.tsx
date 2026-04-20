import { Moon, Sun } from "lucide-react";
import { useSession } from "../stores/session";

export function ThemeToggle() {
  const theme = useSession((s) => s.theme);
  const toggle = useSession((s) => s.toggleTheme);
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      title={theme === "dark" ? "Light mode" : "Dark mode"}
    >
      {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      <span>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
