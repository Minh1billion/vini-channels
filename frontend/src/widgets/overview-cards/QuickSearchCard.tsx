import { ArrowRight, AtSign, Clapperboard, Handshake } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SearchBox } from '@/features/global-search/SearchBox';

const shortcuts = [
  { to: '/partners', label: 'Đối tác', icon: Handshake },
  { to: '/channels', label: 'Kênh', icon: AtSign },
  { to: '/videos', label: 'Video', icon: Clapperboard },
];

export function QuickSearchCard() {
  return (
    <section
      aria-label="Tìm kiếm nhanh"
      className="flex min-h-[134px] flex-col justify-between gap-4 rounded-card border border-border bg-card p-4"
    >
      <SearchBox />
      <ul className="flex flex-wrap items-center gap-2">
        {shortcuts.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <Link
              to={to}
              className="inline-flex h-8 items-center gap-1.5 rounded-full border border-border bg-card px-3 text-[13px] font-medium text-fg hover:bg-surface"
            >
              <Icon className="h-3.5 w-3.5" aria-hidden />
              {label}
              <ArrowRight className="h-3 w-3" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
