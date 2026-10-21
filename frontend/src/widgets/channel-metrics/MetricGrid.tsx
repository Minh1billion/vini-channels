import {
  Activity,
  Bookmark,
  CalendarDays,
  Clapperboard,
  Clock,
  Crown,
  Eye,
  Film,
  Flame,
  Gauge,
  Heart,
  HelpCircle,
  Layers,
  MessageCircle,
  Radio,
  Repeat,
  Scale,
  Share2,
  Sigma,
  Sparkles,
  Target,
  ThumbsUp,
  Timer,
  TrendingDown,
  TrendingUp,
  UserPlus,
  Users,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import type { Facts } from '@/entities/analytics/insights';
import { WEEKDAY_NAMES, hourRange } from '@/entities/analytics/insights';
import { changeRatio, signedCount, signedPercent } from '@/entities/analytics/kpis';
import type { ChannelMetrics } from '@/entities/analytics/types';
import { cn } from '@/shared/lib/cn';
import { clock, compact, full, percent } from '@/shared/lib/format';
import { Button, Skeleton, Widget } from '@/shared/ui';
import { NeedsBadge } from '@/widgets/data-readiness/DataReadiness';

export interface Profile {
  followers: number;
  totalLikes: number;
  videoCount: number;
}

interface Delta {
  text: string;
  down: boolean;
}

interface Item {
  label: string;
  icon: LucideIcon;
  value: string;
  note: string;
  delta?: Delta | null;
  previous?: string;
  hint?: string;
  many?: boolean;
}

interface Group {
  title: string;
  icon: LucideIcon;
  items: Item[];
}

const COMPARE = 'so với kỳ trước';

const countDelta = (current: number | null, previous: number | null): Delta | null => {
  if (current === null || previous === null || previous === 0) return null;
  const ratio = changeRatio(current, previous);
  const text = signedPercent(ratio);
  return text === null || ratio === null ? null : { text, down: ratio < 0 };
};

const rateDelta = (current: number | null, previous: number | null): Delta | null => {
  if (current === null || previous === null) return null;
  const diff = (current - previous) * 100;
  const text = `${diff > 0 ? '+' : ''}${diff.toFixed(1).replace('.', ',')} điểm %`;
  return { text, down: diff < 0 };
};

const perWeek = (value: number | null) => (value === null ? '—' : value.toFixed(1).replace('.', ','));

function buildGroups(data: ChannelMetrics, facts: Facts | null, profile: Profile | null): Group[] {
  const { current: now, previous: before } = data;
  const compare = COMPARE;
  const groups: Group[] = [
    {
      title: 'Hiệu quả nội dung',
      icon: Gauge,
      items: [
        {
          label: 'Tổng lượt xem',
          icon: Eye,
          previous: compact(before.total_views),
          value: compact(now.total_views),
          delta: countDelta(now.total_views, before.total_views),
          hint: compare,
          note: 'Tổng lượt xem hiện tại của các video đăng trong kỳ.',
        },
        {
          label: 'Lượt xem TB / video',
          icon: Sigma,
          previous: compact(before.average_views),
          value: compact(now.average_views),
          delta: countDelta(now.average_views, before.average_views),
          hint: compare,
          note: 'Tổng lượt xem chia số video. Dễ bị kéo lên bởi vài video đột biến.',
        },
        {
          label: 'Lượt xem trung vị',
          icon: Scale,
          previous: compact(before.median_views),
          value: compact(now.median_views),
          delta: countDelta(now.median_views, before.median_views),
          hint: compare,
          note: 'Mức lượt xem điển hình của một video, ít bị lệch bởi video đột biến.',
        },
        {
          label: 'Tỉ lệ video viral',
          icon: Flame,
          previous: percent(before.viral_rate),
          value: percent(now.viral_rate),
          delta: rateDelta(now.viral_rate, before.viral_rate),
          hint: compare,
          note: 'Tỉ lệ video đạt lượt xem từ 3 lần trung vị trở lên.',
        },
        {
          label: 'Tập trung vào top 3',
          icon: Crown,
          value: percent(facts?.topShare),
          hint: 'trên tổng lượt xem',
          note: 'Phần lượt xem đến từ 3 video hàng đầu. Càng cao càng phụ thuộc vào ít video.',
        },
      ],
    },
    {
      title: 'Tương tác',
      icon: Zap,
      items: [
        {
          label: 'Tỉ lệ tương tác (ERV)',
          icon: Activity,
          previous: percent(before.erv),
          value: percent(now.erv),
          delta: rateDelta(now.erv, before.erv),
          hint: compare,
          note: '(Thích + bình luận + chia sẻ) / lượt xem.',
        },
        {
          label: 'Tương tác / người theo dõi',
          icon: Users,
          previous: percent(before.erf),
          value: percent(now.erf),
          delta: rateDelta(now.erf, before.erf),
          hint: compare,
          note: 'Tương tác trung bình mỗi video so với số người theo dõi.',
        },
        {
          label: 'Tỉ lệ thích',
          icon: ThumbsUp,
          previous: percent(before.like_rate, 2),
          value: percent(now.like_rate, 2),
          delta: rateDelta(now.like_rate, before.like_rate),
          hint: compare,
          note: 'Lượt thích / lượt xem.',
        },
        {
          label: 'Tỉ lệ bình luận',
          icon: MessageCircle,
          previous: percent(before.comment_rate, 2),
          value: percent(now.comment_rate, 2),
          delta: rateDelta(now.comment_rate, before.comment_rate),
          hint: compare,
          note: 'Bình luận / lượt xem. Phản ánh mức độ gợi thảo luận.',
        },
        {
          label: 'Tỉ lệ chia sẻ',
          icon: Share2,
          previous: percent(before.share_rate, 2),
          value: percent(now.share_rate, 2),
          delta: rateDelta(now.share_rate, before.share_rate),
          hint: compare,
          note: 'Chia sẻ / lượt xem. Phản ánh khả năng lan truyền.',
        },
        {
          label: 'Lượt lưu',
          icon: Bookmark,
          value: facts?.saves === null || facts === null ? '—' : compact(facts.saves),
          hint: 'tổng trong kỳ',
          note: 'Tổng lượt lưu video, chỉ có khi nguồn dữ liệu cung cấp.',
        },
      ],
    },
    {
      title: 'Tần suất và lan toả',
      icon: Radio,
      items: [
        {
          label: 'Video / tuần',
          icon: Repeat,
          previous: perWeek(before.posts_per_week),
          value: perWeek(now.posts_per_week),
          delta: countDelta(now.posts_per_week, before.posts_per_week),
          hint: compare,
          note: 'Nhịp đăng trung bình trong kỳ.',
        },
        {
          label: 'Tiếp cận / người theo dõi',
          icon: Target,
          previous: percent(before.reach_ratio),
          value: percent(now.reach_ratio),
          hint: 'lượt xem TB / follower',
          note: 'Trên 100% nghĩa là video thường vượt ra ngoài tệp người theo dõi.',
        },
        {
          label: 'Tăng người theo dõi',
          icon: UserPlus,
          previous: signedCount(before.follower_growth),
          value: signedCount(now.follower_growth),
          delta: growthRatio(now.follower_growth_ratio),
          hint: 'trong kỳ',
          many: true,
          note: 'Chênh lệch người theo dõi giữa lần đồng bộ đầu và cuối kỳ.',
        },
        {
          label: 'Thời lượng TB',
          icon: Timer,
          value: clock(facts?.averageDuration),
          hint: 'phút:giây',
          note: 'Thời lượng trung bình của các video trong kỳ.',
        },
        {
          label: 'Ngày đăng hiệu quả nhất',
          icon: CalendarDays,
          value: facts?.bestWeekday ? WEEKDAY_NAMES[facts.bestWeekday.index] : '—',
          hint: facts?.bestWeekday ? `TB ${compact(facts.bestWeekday.average)} · ${facts.bestWeekday.count} video` : undefined,
          note: 'Ngày trong tuần có lượt xem trung bình cao nhất (ưu tiên ngày có từ 2 video).',
        },
        {
          label: 'Giờ đăng hiệu quả nhất',
          icon: Clock,
          value: facts?.bestHour ? hourRange(facts.bestHour.index) : '—',
          hint: facts?.bestHour ? `TB ${compact(facts.bestHour.average)} · ${facts.bestHour.count} video` : undefined,
          note: 'Giờ trong ngày có lượt xem trung bình cao nhất (ưu tiên giờ có từ 2 video).',
        },
      ],
    },
  ];
  if (profile) {
    groups.push({
      title: 'Hồ sơ kênh (lần đồng bộ gần nhất)',
      icon: Layers,
      items: [
        {
          label: 'Tổng lượt thích của kênh',
          icon: Heart,
          value: compact(profile.totalLikes),
          hint: 'từ trước đến nay',
          note: 'Tổng lượt thích mọi video của kênh, theo số liệu hồ sơ kênh.',
        },
        {
          label: 'Tổng video của kênh',
          icon: Clapperboard,
          value: full(profile.videoCount),
          hint: 'từ trước đến nay',
          note: 'Số video công khai trên kênh.',
        },
        {
          label: 'Thích / video',
          icon: Film,
          value: profile.videoCount > 0 ? compact(profile.totalLikes / profile.videoCount) : '—',
          hint: 'trung bình toàn kênh',
          note: 'Tổng lượt thích chia tổng số video.',
        },
        {
          label: 'Thích / người theo dõi',
          icon: Sparkles,
          value: profile.followers > 0 ? (profile.totalLikes / profile.followers).toFixed(1).replace('.', ',') : '—',
          hint: 'lượt thích mỗi follower',
          note: 'Tổng lượt thích chia số người theo dõi. Cao nghĩa là nội dung được yêu thích bền vững.',
        },
      ],
    });
  }
  return groups;
}

function growthRatio(ratio: number | null): Delta | null {
  const text = signedPercent(ratio);
  return text === null || ratio === null ? null : { text, down: ratio < 0 };
}

const TIP_WIDTH = 296;

interface Tip {
  item: Item;
  left: number;
  top?: number;
  bottom?: number;
}

function Trend({ delta }: { delta: Delta }) {
  const Icon = delta.down ? TrendingDown : TrendingUp;
  return (
    <span className={cn('inline-flex items-center gap-1 font-medium', delta.down ? 'text-down' : 'text-blue')}>
      <Icon className="h-3 w-3" aria-hidden />
      {delta.text}
    </span>
  );
}

function Tooltip({ tip }: { tip: Tip }) {
  const { item } = tip;
  const Glyph = item.icon;
  return (
    <div
      role="tooltip"
      className="pointer-events-none fixed z-50 animate-pop-in rounded-card border border-border bg-card p-3 shadow-pop"
      style={{ left: tip.left, top: tip.top, bottom: tip.bottom, width: TIP_WIDTH }}
    >
      <p className="flex items-center gap-2 text-sm font-bold">
        <span aria-hidden className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-red bg-blue text-on-blue">
          <Glyph className="h-3.5 w-3.5" strokeWidth={2.75} />
        </span>
        {item.label}
      </p>
      <p className="mt-2 text-[13px] leading-5 text-muted">{item.note}</p>
      <dl className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3 text-[13px]">
        <div>
          <dt className="text-muted">Hiện tại</dt>
          <dd className="text-base font-medium">{item.value}</dd>
        </div>
        {item.previous !== undefined ? (
          <div>
            <dt className="text-muted">Kỳ trước</dt>
            <dd className="text-base font-medium">{item.previous}</dd>
          </div>
        ) : null}
      </dl>
      {item.delta ? (
        <p className="mt-2 flex items-center gap-1.5 text-[13px] text-muted">
          <Trend delta={item.delta} />
          so với kỳ trước
        </p>
      ) : null}
    </div>
  );
}

interface CardProps {
  item: Item;
  explain: boolean;
  onShow: (item: Item, element: HTMLElement) => void;
  onHide: () => void;
}

function Card({ item, explain, onShow, onHide }: CardProps) {
  const Glyph = item.icon;
  const hint = item.hint === COMPARE && !item.delta ? null : item.hint;
  return (
    <li
      tabIndex={0}
      onMouseEnter={(event) => onShow(item, event.currentTarget)}
      onFocus={(event) => onShow(item, event.currentTarget)}
      onMouseLeave={onHide}
      onBlur={onHide}
      className="group flex min-w-0 cursor-default flex-col gap-2 rounded-field border border-border bg-surface p-3 transition duration-150 hover:-translate-y-0.5 hover:border-blue hover:bg-card hover:shadow-[0_8px_20px_rgba(1,1,1,0.08)] focus:outline-none focus-visible:ring-2 focus-visible:ring-blue"
    >
      <span className="flex min-h-[34px] items-center gap-2">
        <span
          aria-hidden
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-red bg-blue text-on-blue transition-transform duration-150 group-hover:scale-110"
        >
          <Glyph className="h-4 w-4" strokeWidth={2.75} />
        </span>
        <span className="min-w-0 flex-1 text-[13px] leading-[17px] text-muted transition-colors group-hover:text-fg">{item.label}</span>
      </span>
      <span className="truncate text-xl font-medium">{item.value}</span>
      <span className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-[12px] text-muted">
        {item.delta ? <Trend delta={item.delta} /> : null}
        {hint}
        {item.many ? <NeedsBadge kind="multi" /> : null}
      </span>
      <span className="sr-only">{item.note}</span>
      {explain ? <span className="text-[12px] leading-4 text-muted">{item.note}</span> : null}
    </li>
  );
}

interface Props {
  data?: ChannelMetrics;
  facts: Facts | null;
  profile: Profile | null;
}

export function MetricGrid({ data, facts, profile }: Props) {
  const [explain, setExplain] = useState(false);
  const [tip, setTip] = useState<Tip | null>(null);

  useEffect(() => {
    if (!tip) return undefined;
    const hide = () => setTip(null);
    window.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
    return () => {
      window.removeEventListener('scroll', hide, true);
      window.removeEventListener('resize', hide);
    };
  }, [tip]);

  const show = (item: Item, element: HTMLElement) => {
    const box = element.getBoundingClientRect();
    const left = Math.min(Math.max(8, box.left + box.width / 2 - TIP_WIDTH / 2), window.innerWidth - TIP_WIDTH - 8);
    const below = box.bottom + 8 + 210 <= window.innerHeight;
    setTip(
      below
        ? { item, left, top: box.bottom + 8 }
        : { item, left, bottom: window.innerHeight - box.top + 8 },
    );
  };
  const groups = data ? buildGroups(data, facts, profile) : null;

  return (
    <Widget
      title="Chỉ số chi tiết"
      actions={
        <Button size="sm" variant={explain ? 'accent' : 'ghost'} aria-pressed={explain} onClick={() => setExplain((value) => !value)}>
          <HelpCircle className="h-4 w-4" aria-hidden />
          Giải thích chỉ số
        </Button>
      }
      bodyClassName="flex flex-col gap-5 p-4"
    >
      {groups ? (
        groups.map((group) => (
          <section key={group.title} aria-label={group.title} className="flex flex-col gap-2">
            <h3 className="flex items-center gap-1.5 text-[13px] font-bold uppercase tracking-wide text-muted">
              <group.icon className="h-4 w-4" aria-hidden />
              {group.title}
            </h3>
            <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {group.items.map((item) => (
                <Card key={item.label} item={item} explain={explain} onShow={show} onHide={() => setTip(null)} />
              ))}
            </ul>
          </section>
        ))
      ) : (
        <Skeleton className="h-[320px]" />
      )}
      {tip ? <Tooltip tip={tip} /> : null}
    </Widget>
  );
}
