import { ArrowDownWideNarrow, ArrowUpDown, ArrowUpNarrowWide, AtSign, Search, Clapperboard } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { VideoSort } from '@/entities/analytics/types';
import { analyticsApi, channelsApi } from '@/shared/api';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { errorMessage } from '@/shared/lib/errors';
import { lastDays, periodKey, type Period } from '@/shared/lib/period';
import { useAsync } from '@/shared/lib/useAsync';
import { useDebounced } from '@/shared/lib/useDebounced';
import { Button, FormError, IconButton, Pagination, SelectField } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';
import { VideoGrid } from '@/widgets/video-grid/VideoGrid';

const SORTS: Array<{ id: VideoSort; label: string }> = [
  { id: 'posted', label: 'Ngày đăng' },
  { id: 'views', label: 'Lượt xem' },
  { id: 'likes', label: 'Lượt thích' },
  { id: 'comments', label: 'Bình luận' },
  { id: 'shares', label: 'Chia sẻ' },
  { id: 'erv', label: 'Tỉ lệ tương tác' },
];

const PAGE_SIZE = 24;

export function VideosPage() {
  const [query, setQuery] = useState('');
  const [channelId, setChannelId] = useState('');
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const periodId = periodKey(period);
  const [sort, setSort] = useState<VideoSort>('posted');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const debounced = useDebounced(query);

  const channels = useAsync(() => channelsApi.list(), []);
  const videos = useAsync(
    () =>
      analyticsApi.videoPage({
        channel_id: channelId,
        period,
        q: debounced,
        sort,
        order,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      }),
    [channelId, periodId, debounced, sort, order, page],
  );

  const total = videos.data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const firstShown = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const lastShown = Math.min(page * PAGE_SIZE, total);

  useEffect(() => {
    if (videos.data && page > pageCount) setPage(pageCount);
  }, [videos.data, page, pageCount]);

  const changePage = (next: number) => {
    setPage(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const withReset =
    <T,>(set: (value: T) => void) =>
    (value: T) => {
      set(value);
      setPage(1);
    };

  return (
    <>
      <PageHeader
        icon={Clapperboard}
        title="Video"
        description="Video mới từ các kênh đang theo dõi, lọc theo khoảng thời gian."
      />

      <div className="mb-4">
        <RangePicker value={period} onChange={withReset(setPeriod)} />
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label className="relative w-full max-w-xs">
          <span className="sr-only">Tìm video</span>
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(event) => withReset(setQuery)(event.target.value)}
            placeholder="Tìm theo chú thích hoặc kênh..."
            className="h-10 w-full rounded-field border border-border bg-card pl-8 pr-3 text-sm placeholder:text-muted focus:border-fg focus:outline-none"
          />
        </label>
        <SelectField label="Kênh" hideLabel icon={AtSign} value={channelId} onChange={(e) => withReset(setChannelId)(e.target.value)} className="w-full sm:w-56">
          <option value="">Tất cả kênh</option>
          {(channels.data ?? []).map((channel) => (
            <option key={channel.id} value={channel.id}>
              @{channel.handle}
            </option>
          ))}
        </SelectField>
        <SelectField label="Sắp xếp theo" hideLabel icon={ArrowUpDown} value={sort} onChange={(e) => withReset(setSort)(e.target.value as VideoSort)} className="w-full sm:w-64">
          {SORTS.map((item) => (
            <option key={item.id} value={item.id}>
              Xếp theo {item.label.toLowerCase()}
            </option>
          ))}
        </SelectField>
        <IconButton
          bordered
          label={order === 'desc' ? 'Đang xếp giảm dần, bấm để xếp tăng dần' : 'Đang xếp tăng dần, bấm để xếp giảm dần'}
          onClick={() => withReset(setOrder)(order === 'desc' ? 'asc' : 'desc')}
          className="h-10 w-10"
        >
          {order === 'desc' ? (
            <ArrowDownWideNarrow className="h-4 w-4" aria-hidden />
          ) : (
            <ArrowUpNarrowWide className="h-4 w-4" aria-hidden />
          )}
        </IconButton>
      </div>

      {videos.error ? (
        <div className="flex items-center gap-3">
          <FormError message={errorMessage(videos.error)} />
          <Button variant="primary" onClick={videos.reload}>Thử lại</Button>
        </div>
      ) : (
        <>
          <div className={videos.loading && videos.data ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
            <VideoGrid
              videos={videos.data?.items}
              emptyDescription={
                debounced || channelId
                  ? 'Không có video khớp bộ lọc.'
                  : 'Chưa có video nào trong khoảng này. Đồng bộ kênh để lấy dữ liệu.'
              }
            />
          </div>
          {total > 0 ? (
            <div className="mt-6 flex flex-col items-center gap-3">
              <p className="text-sm text-muted">
                Hiển thị {firstShown}–{lastShown} / {total} video
              </p>
              <Pagination page={page} pageCount={pageCount} onChange={changePage} disabled={videos.loading} />
            </div>
          ) : null}
        </>
      )}
    </>
  );
}
