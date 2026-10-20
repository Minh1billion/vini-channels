import { X } from 'lucide-react';
import { useId, useState, type KeyboardEvent } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props {
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  hint?: string;
  className?: string;
}

const normalize = (tag: string) => tag.trim().toLowerCase();

export function TagInputField({ label, value, onChange, placeholder, hint, className }: Props) {
  const id = useId();
  const [draft, setDraft] = useState('');

  const commit = () => {
    const next = normalize(draft);
    setDraft('');
    if (next && !value.includes(next)) onChange([...value, next]);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.nativeEvent.isComposing) return;
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      commit();
    } else if (event.key === 'Backspace' && draft === '' && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <div className="flex min-h-10 flex-wrap items-center gap-1.5 rounded-field border border-border bg-card px-2 py-1.5 focus-within:border-fg">
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex h-7 items-center gap-1 rounded-full border border-border bg-card pl-3 pr-1 text-[13px] font-medium"
          >
            {tag}
            <button
              type="button"
              aria-label={`Xóa nhãn ${tag}`}
              onClick={() => onChange(value.filter((item) => item !== tag))}
              className="inline-flex h-5 w-5 items-center justify-center rounded-full text-up hover:bg-surface"
            >
              <X className="h-3.5 w-3.5" aria-hidden />
            </button>
          </span>
        ))}
        <input
          id={id}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
          onBlur={commit}
          placeholder={value.length === 0 ? placeholder : undefined}
          maxLength={40}
          className="h-7 min-w-[120px] flex-1 bg-transparent px-1 text-sm placeholder:text-muted focus:outline-none"
        />
      </div>
      {hint ? <p className="text-[13px] text-muted">{hint}</p> : null}
    </div>
  );
}
