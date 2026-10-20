import { useId, useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { Chip } from './Chip';

interface Props {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  otherLabel?: string;
  otherPlaceholder?: string;
  hint?: string;
  className?: string;
}

export function ChipSelectField({
  label,
  value,
  options,
  onChange,
  otherLabel = 'Khác',
  otherPlaceholder = 'Nhập cụ thể',
  hint,
  className,
}: Props) {
  const id = useId();
  const [otherOpen, setOtherOpen] = useState(value !== '' && !options.includes(value));

  const pick = (option: string) => {
    setOtherOpen(false);
    onChange(value === option && !otherOpen ? '' : option);
  };

  const toggleOther = () => {
    setOtherOpen(!otherOpen);
    onChange('');
  };

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <span id={`${id}-label`} className="text-sm font-medium">
        {label}
      </span>
      <div role="group" aria-labelledby={`${id}-label`} className="flex flex-wrap gap-2">
        {options.map((option) => (
          <Chip key={option} active={!otherOpen && value === option} onClick={() => pick(option)}>
            {option}
          </Chip>
        ))}
        <Chip active={otherOpen} onClick={toggleOther}>
          {otherLabel}
        </Chip>
      </div>
      {otherOpen ? (
        <input
          aria-label={`${label}: ${otherLabel.toLowerCase()}`}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={otherPlaceholder}
          maxLength={80}
          autoFocus={value === ''}
          className="h-10 w-full rounded-field border border-border bg-card px-3 text-sm placeholder:text-muted focus:border-fg focus:outline-none"
        />
      ) : null}
      {hint ? <p className="text-[13px] text-muted">{hint}</p> : null}
    </div>
  );
}
