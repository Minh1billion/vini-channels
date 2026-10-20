import { Moon, Sun } from 'lucide-react';
import { useState } from 'react';
import { applyTheme, readTheme, type Theme } from '@/shared/lib/theme';
import { IconButton } from '@/shared/ui';

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readTheme);
  const next: Theme = theme === 'light' ? 'dark' : 'light';

  return (
    <IconButton
      bordered
      label={next === 'dark' ? 'Chuyển sang chế độ tối' : 'Chuyển sang chế độ sáng'}
      onClick={() => {
        applyTheme(next);
        setTheme(next);
      }}
    >
      {theme === 'light' ? <Moon className="h-4 w-4" aria-hidden /> : <Sun className="h-4 w-4" aria-hidden />}
    </IconButton>
  );
}
