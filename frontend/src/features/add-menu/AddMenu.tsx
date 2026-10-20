import { AtSign, ChevronDown, Handshake, Link2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/AuthProvider';
import { Button, Menu, MenuItem, MenuSeparator } from '@/shared/ui';

export function AddMenu() {
  const navigate = useNavigate();
  const { can } = useAuth();
  if (!can('partners:write')) return null;
  return (
    <Menu
      trigger={({ open, toggle }) => (
        <Button variant="primary" aria-haspopup="menu" aria-expanded={open} onClick={toggle}>
          Thêm
          <ChevronDown className="h-4 w-4" aria-hidden />
        </Button>
      )}
    >
      {(close) => (
        <>
          <MenuItem icon={Handshake} onSelect={() => { close(); navigate('/partners?new=1'); }}>
            Thêm đối tác
          </MenuItem>
          <MenuItem icon={AtSign} onSelect={() => { close(); navigate('/channels?new=1'); }}>
            Thêm kênh
          </MenuItem>
          <MenuSeparator />
          <MenuItem icon={Link2} onSelect={() => { close(); navigate('/channels'); }}>
            Gửi liên kết cấp quyền
          </MenuItem>
        </>
      )}
    </Menu>
  );
}
