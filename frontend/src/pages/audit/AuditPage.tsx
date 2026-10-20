import { ScrollText, ShieldOff } from 'lucide-react';
import { useMemo, useState } from 'react';
import { actionLabels, actionOptions, detailLines } from '@/entities/audit/model';
import type { AuditEntry } from '@/entities/audit/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { auditApi, usersApi } from '@/shared/api';
import { dateTimeYear } from '@/shared/lib/format';
import { errorMessage } from '@/shared/lib/errors';
import { useAsync } from '@/shared/lib/useAsync';
import { Button, DataTable, EmptyState, SelectField, Skeleton, TextField, Widget, type Column } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

const PAGE_SIZE = 100;

const columns: Array<Column<AuditEntry>> = [
  {
    key: 'time',
    header: 'Thời gian',
    cell: (row) => <span className="whitespace-nowrap">{dateTimeYear(new Date(row.occurred_at))}</span>,
  },
  { key: 'actor', header: 'Người thực hiện', cell: (row) => row.actor_email },
  {
    key: 'action',
    header: 'Thao tác',
    cell: (row) => <span className="font-medium">{actionLabels[row.action] ?? row.action}</span>,
  },
  { key: 'target', header: 'Đối tượng', cell: (row) => row.target_label || row.target_id },
  {
    key: 'detail',
    header: 'Chi tiết',
    cell: (row) => {
      const lines = detailLines(row.detail);
      return lines.length === 0 ? (
        <span className="text-muted">—</span>
      ) : (
        <ul className="flex flex-col gap-0.5">
          {lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      );
    },
  },
];

function AuditTable() {
  const [actorId, setActorId] = useState('');
  const [action, setAction] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [limit, setLimit] = useState(PAGE_SIZE);

  const users = useAsync(() => usersApi.list(), []);
  const query = useMemo(
    () => ({ actor_id: actorId, action, date_from: dateFrom, date_to: dateTo, limit }),
    [actorId, action, dateFrom, dateTo, limit],
  );
  const { data, loading, error, reload } = useAsync(() => auditApi.list(query), [query]);

  const reset = <T,>(setter: (value: T) => void) => (value: T) => {
    setter(value);
    setLimit(PAGE_SIZE);
  };

  return (
    <>
      <PageHeader
        icon={ScrollText}
        title="Nhật ký hoạt động"
        description="Lịch sử thao tác của người dùng và hệ thống."
      />

      <Widget>
        <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <SelectField label="Người thực hiện" value={actorId} onChange={(e) => reset(setActorId)(e.target.value)}>
            <option value="">Tất cả</option>
            <option value="system">Hệ thống</option>
            {(users.data ?? []).map((user) => (
              <option key={user.id} value={user.id}>
                {user.email}
              </option>
            ))}
          </SelectField>
          <SelectField label="Loại thao tác" value={action} onChange={(e) => reset(setAction)(e.target.value)}>
            <option value="">Tất cả</option>
            {actionOptions.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </SelectField>
          <TextField
            label="Từ ngày"
            type="date"
            value={dateFrom}
            max={dateTo || undefined}
            onChange={(e) => reset(setDateFrom)(e.target.value)}
          />
          <TextField
            label="Đến ngày"
            type="date"
            value={dateTo}
            min={dateFrom || undefined}
            onChange={(e) => reset(setDateTo)(e.target.value)}
          />
        </div>
      </Widget>

      <Widget>
        {!data && loading ? (
          <div className="flex flex-col gap-2 p-4">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            icon={ScrollText}
            title="Không tải được nhật ký"
            description={errorMessage(error)}
            action={<Button variant="secondary" onClick={reload}>Thử lại</Button>}
          />
        ) : (data ?? []).length === 0 ? (
          <EmptyState icon={ScrollText} title="Chưa có hoạt động nào" description="Thử đổi bộ lọc để xem thêm." />
        ) : (
          <>
            <DataTable columns={columns} rows={data ?? []} rowKey={(row) => row.id} caption="Nhật ký hoạt động" />
            {(data ?? []).length >= limit ? (
              <div className="flex justify-center p-4">
                <Button variant="secondary" onClick={() => setLimit(limit + PAGE_SIZE)} disabled={loading}>
                  Xem thêm
                </Button>
              </div>
            ) : null}
          </>
        )}
      </Widget>
    </>
  );
}

export function AuditPage() {
  const { can } = useAuth();
  if (!can('audit:read')) {
    return (
      <>
        <PageHeader
        icon={ScrollText}
        title="Nhật ký hoạt động"
        description="Lịch sử thao tác của người dùng và hệ thống."
      />
        <Widget>
          <EmptyState
            icon={ShieldOff}
            title="Bạn không có quyền"
            description="Chỉ quản trị viên mới xem được nhật ký hoạt động."
          />
        </Widget>
      </>
    );
  }
  return <AuditTable />;
}
