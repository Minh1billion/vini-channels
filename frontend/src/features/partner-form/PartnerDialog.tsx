import { useState } from 'react';
import type { Partner } from '@/entities/partner/types';
import { partnersApi } from '@/shared/api';
import { ChipSelectField, FormDialog, TagInputField, TextAreaField, TextField } from '@/shared/ui';

interface Props {
  partner: Partner | null;
  onClose: () => void;
  onSaved: () => void;
}

const INDUSTRIES = [
  'Thời trang',
  'F&B',
  'Mỹ phẩm',
  'Công nghệ',
  'Giáo dục',
  'Du lịch',
  'Bất động sản',
  'Tài chính',
  'Sức khỏe',
  'Giải trí',
  'Thương mại điện tử',
];

export function PartnerDialog({ partner, onClose, onSaved }: Props) {
  const [name, setName] = useState(partner?.name ?? '');
  const [industry, setIndustry] = useState(partner?.industry ?? '');
  const [tags, setTags] = useState<string[]>(partner?.tags ?? []);
  const [notes, setNotes] = useState(partner?.notes ?? '');

  const submit = async () => {
    const body = {
      name: name.trim(),
      industry: industry.trim() || null,
      tags,
      notes: notes.trim(),
    };
    if (partner) await partnersApi.update(partner.id, body);
    else await partnersApi.create(body);
    onSaved();
  };

  return (
    <FormDialog
      title={partner ? 'Sửa đối tác' : 'Thêm đối tác'}
      submitLabel={partner ? 'Lưu' : 'Thêm đối tác'}
      canSubmit={Boolean(name.trim())}
      onSubmit={submit}
      onClose={onClose}
    >
      <TextField
        label="Tên đối tác"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="VD: Công ty Thời trang ABC"
        required
        autoFocus
      />
      <ChipSelectField
        label="Ngành"
        value={industry}
        options={INDUSTRIES}
        onChange={setIndustry}
        otherPlaceholder="VD: Nội thất, Thú cưng..."
      />
      <TagInputField
        label="Nhãn"
        value={tags}
        onChange={setTags}
        placeholder="VD: vip, ký hợp đồng 2026"
        hint="Nhập rồi nhấn Enter để thêm nhãn"
      />
      <TextAreaField
        label="Ghi chú"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Đầu mối liên hệ, thỏa thuận hợp tác, lưu ý khi làm việc..."
      />
    </FormDialog>
  );
}
