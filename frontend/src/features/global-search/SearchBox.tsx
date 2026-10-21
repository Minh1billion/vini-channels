import { AtSign, Clapperboard, Handshake, Search, X, type LucideIcon } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import type { SearchResults } from '@/entities/search/types';
import { searchApi } from '@/shared/api';
import { cn } from '@/shared/lib/cn';
import { errorMessage } from '@/shared/lib/errors';
import { useDebounced } from '@/shared/lib/useDebounced';
import { IconButton, Kbd } from '@/shared/ui';
import { useSearchRegistry } from './GlobalSearchProvider';

interface Item {
  key: string;
  group: string;
  icon: LucideIcon;
  title: string;
  subtitle: string;
  to: string;
}

const MIN_LENGTH = 2;

const toItems = (results: SearchResults | null): Item[] => {
  if (!results) return [];
  return [
    ...results.partners.map((partner) => ({
      key: `partner-${partner.id}`,
      group: 'Đối tác',
      icon: Handshake,
      title: partner.name,
      subtitle: partner.industry ?? `${partner.channel_count} kênh`,
      to: `/partners?q=${encodeURIComponent(partner.name)}`,
    })),
    ...results.channels.map((channel) => ({
      key: `channel-${channel.id}`,
      group: 'Kênh',
      icon: AtSign,
      title: channel.display_name || channel.handle,
      subtitle: channel.handle,
      to: `/channels/${channel.id}`,
    })),
    ...results.videos.map((video) => ({
      key: `video-${video.id}`,
      group: 'Video',
      icon: Clapperboard,
      title: video.caption || 'Video không có mô tả',
      subtitle: video.handle,
      to: `/channels/${video.channel_id}?tab=videos&video=${encodeURIComponent(video.id)}`,
    })),
  ];
};

interface Props {
  variant?: 'field' | 'icon';
  appearance?: 'pill' | 'box';
  className?: string;
  onNavigate?: () => void;
}

export function SearchBox({ variant = 'field', appearance = 'box', className, onNavigate }: Props) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cursor, setCursor] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const listId = useId();
  const navigate = useNavigate();
  const { register } = useSearchRegistry();
  const trimmed = query.trim();
  const debounced = useDebounced(trimmed, 200);
  const isIcon = variant === 'icon';

  useEffect(() => {
    return register(() => {
      if (!root.current || root.current.offsetParent === null) return false;
      setOpen(true);
      requestAnimationFrame(() => input.current?.focus());
      return true;
    });
  }, [register]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onPointer);
    return () => document.removeEventListener('mousedown', onPointer);
  }, [open]);

  useEffect(() => {
    if (debounced.length < MIN_LENGTH) {
      setResults(null);
      setLoading(false);
      setError(null);
      return;
    }
    let active = true;
    setLoading(true);
    searchApi
      .query(debounced)
      .then((data) => {
        if (!active) return;
        setResults(data);
        setError(null);
        setCursor(0);
      })
      .catch((err: unknown) => {
        if (active) setError(errorMessage(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [debounced]);

  const items = useMemo(() => toItems(results), [results]);

  useEffect(() => {
    listRef.current?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: 'nearest' });
  }, [cursor]);

  const close = () => {
    setOpen(false);
    setQuery('');
    setResults(null);
  };

  const choose = (item: Item) => {
    close();
    input.current?.blur();
    onNavigate?.();
    navigate(item.to);
  };

  const onKeyDown = (event: ReactKeyboardEvent) => {
    if (event.key === 'Escape' && open) {
      event.preventDefault();
      setOpen(false);
      input.current?.blur();
    } else if (event.key === 'ArrowDown' && items.length > 0) {
      event.preventDefault();
      setOpen(true);
      setCursor((value) => (value + 1) % items.length);
    } else if (event.key === 'ArrowUp' && items.length > 0) {
      event.preventDefault();
      setCursor((value) => (value - 1 + items.length) % items.length);
    } else if (event.key === 'Enter') {
      const item = items[cursor];
      if (item && open) {
        event.preventDefault();
        choose(item);
      }
    }
  };

  const typed = trimmed.length >= MIN_LENGTH;
  const settled = typed && debounced === trimmed && !loading && !error;
  const activeId = items[cursor] ? `${listId}-${items[cursor].key}` : undefined;

  const inputRow = (
    <div
      className={cn(
        'relative flex h-10 items-center gap-2 pl-3 pr-2 text-sm transition-colors',
        isIcon
          ? 'border-b border-border'
          : appearance === 'pill'
            ? cn('rounded-full bg-surface', open && 'ring-2 ring-[var(--focus)]')
            : cn('rounded-field border bg-card', open ? 'border-fg' : 'border-border hover:border-fg'),
      )}
    >
      <Search className="h-4 w-4 shrink-0 text-muted" aria-hidden />
      <input
        ref={input}
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={isIcon ? 'Tìm đối tác, kênh, video...' : appearance === 'pill' ? 'Tìm kiếm...' : 'Tìm đối tác, kênh, video...'}
        aria-label="Từ khóa tìm kiếm"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open ? activeId : undefined}
        autoComplete="off"
        className="h-full min-w-0 flex-1 bg-transparent text-sm placeholder:text-muted focus:outline-none"
      />
      {query ? (
        <button
          type="button"
          aria-label="Xóa từ khóa"
          onClick={() => {
            setQuery('');
            input.current?.focus();
          }}
          className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-muted transition-colors hover:bg-card hover:text-fg"
        >
          <X className="h-3.5 w-3.5" aria-hidden />
        </button>
      ) : (
        <Kbd>{open ? 'Esc' : '⌘ K'}</Kbd>
      )}
    </div>
  );

  const results_ = (
    <div className="max-h-[min(60vh,420px)] overflow-y-auto p-2">
      {!typed ? (
        <p className="px-2 py-5 text-center text-[13px] text-muted">Nhập ít nhất {MIN_LENGTH} ký tự để tìm kiếm.</p>
      ) : null}
      {error ? (
        <p role="alert" className="px-2 py-5 text-center text-sm text-down">
          {error}
        </p>
      ) : null}
      {typed && !error && loading && items.length === 0 ? (
        <p role="status" className="px-2 py-5 text-center text-[13px] text-muted">
          Đang tìm...
        </p>
      ) : null}
      {settled && items.length === 0 ? (
        <p className="px-2 py-5 text-center text-[13px] text-muted">Không có kết quả phù hợp.</p>
      ) : null}
      <ul ref={listRef} id={listId} role="listbox" aria-label="Kết quả tìm kiếm" className="flex flex-col">
        {items.map((item, index) => {
          const Icon = item.icon;
          const showGroup = index === 0 || items[index - 1]?.group !== item.group;
          return (
            <li key={item.key} role="presentation">
              {showGroup ? (
                <p className="px-2 pb-1 pt-2 text-[12px] font-medium uppercase tracking-wide text-muted">{item.group}</p>
              ) : null}
              <button
                type="button"
                id={`${listId}-${item.key}`}
                role="option"
                aria-selected={index === cursor}
                onMouseEnter={() => setCursor(index)}
                onClick={() => choose(item)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-field px-2 py-2 text-left transition-colors',
                  index === cursor && 'bg-surface',
                )}
              >
                <Icon className="h-4 w-4 shrink-0 text-muted" aria-hidden />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">{item.title}</span>
                  <span className="block truncate text-[13px] text-muted">{item.subtitle}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );

  if (isIcon) {
    return (
      <div ref={root} onKeyDown={onKeyDown} className={cn('relative', className)}>
        <IconButton
          bordered
          label="Tìm kiếm"
          aria-expanded={open}
          onClick={() => {
            setOpen((value) => !value);
            requestAnimationFrame(() => input.current?.focus());
          }}
        >
          <Search className="h-4 w-4" aria-hidden />
        </IconButton>
        {open ? (
          <div className="absolute left-full top-0 z-40 ml-3 w-[22rem] origin-top-left animate-pop-in overflow-hidden rounded-card border border-border bg-card shadow-pop">
            {inputRow}
            {results_}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div ref={root} onKeyDown={onKeyDown} className={cn('relative min-w-0', className)}>
      {inputRow}
      {open ? (
        <div className="absolute left-0 top-full z-40 mt-2 w-[min(28rem,calc(100vw-2rem))] min-w-full origin-top animate-pop-in overflow-hidden rounded-card border border-border bg-card shadow-pop">
          {results_}
        </div>
      ) : null}
    </div>
  );
}
