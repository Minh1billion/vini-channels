import { Construction } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button, EmptyState, Widget } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

export function PlaceholderPage({ title }: { title: string }) {
  const navigate = useNavigate();
  return (
    <>
      <PageHeader icon={Construction} title={title} description="Tính năng đang được phát triển." />
      <Widget>
        <EmptyState
          icon={Construction}
          title="Màn hình này đang được xây dựng"
          description="Nội dung sẽ có ở checkpoint tiếp theo. Quay lại Dashboard để xem phần đã hoàn thành."
          action={<Button variant="primary" onClick={() => navigate('/')}>Về Dashboard</Button>}
        />
      </Widget>
    </>
  );
}
