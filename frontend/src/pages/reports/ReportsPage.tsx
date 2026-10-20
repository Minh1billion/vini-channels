import { Download, FileText } from 'lucide-react';
import { useState } from 'react';
import { partnersApi } from '@/shared/api';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { errorMessage } from '@/shared/lib/errors';
import { lastDays, periodQuery, type Period } from '@/shared/lib/period';
import { useAsync } from '@/shared/lib/useAsync';
import { Button, FormError, SelectField, Widget } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

const EXPORTS = [
  {
    kind: 'channels',
    title: 'Điểm hiệu quả và chỉ số từng kênh',
    description: 'Hạng, điểm tổng, điểm thành phần, tăng trưởng, lượt xem, tỉ lệ tương tác, số bài mỗi tuần.',
  },
  {
    kind: 'videos',
    title: 'Video nổi bật',
    description: '20 video có nhiều lượt xem nhất trong kỳ, kèm lượt thích, bình luận, chia sẻ.',
  },
] as const;

export function ReportsPage() {
  const [partnerId, setPartnerId] = useState('');
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const partners = useAsync(() => partnersApi.list(), []);

  const href = (kind: string) => {
    const params = new URLSearchParams({ kind, ...Object.fromEntries(Object.entries(periodQuery(period)).map(([k, v]) => [k, String(v)])) });
    if (partnerId) params.set('partner_id', partnerId);
    return `/api/v1/reports/export?${params.toString()}`;
  };

  return (
    <>
      <PageHeader
        icon={FileText}
        title="Báo cáo"
        description="Xuất báo cáo hiệu quả theo đối tác và khoảng thời gian."
      />
      <div className="flex flex-col gap-6">
        <Widget title="Phạm vi báo cáo" bodyClassName="flex flex-col gap-4 p-4">
          {partners.error ? <FormError message={errorMessage(partners.error)} /> : null}
          <SelectField
            label="Đối tác"
            value={partnerId}
            onChange={(event) => setPartnerId(event.target.value)}
            className="max-w-sm"
          >
            <option value="">Tất cả đối tác</option>
            {(partners.data ?? []).map((partner) => (
              <option key={partner.id} value={partner.id}>
                {partner.name}
              </option>
            ))}
          </SelectField>
          <RangePicker value={period} onChange={setPeriod} />
        </Widget>

        <Widget title="Xuất CSV" bodyClassName="divide-y divide-border">
          {EXPORTS.map((item) => (
            <div key={item.kind} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <h3 className="text-sm font-bold">{item.title}</h3>
                <p className="text-sm text-muted">{item.description}</p>
              </div>
              <a href={href(item.kind)} download>
                <Button variant="primary">
                  <Download className="h-4 w-4" aria-hidden />
                  Tải CSV
                </Button>
              </a>
            </div>
          ))}
        </Widget>
      </div>
    </>
  );
}
