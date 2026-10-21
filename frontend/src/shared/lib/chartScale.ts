export interface Scale {
  lower: number;
  upper: number;
  ticks: number[];
}

interface Options {
  zeroBased?: boolean;
  minSpanRatio?: number;
  targetTicks?: number;
}

function niceStep(raw: number) {
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normalized = raw / magnitude;
  const factor = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return Math.max(1, factor * magnitude);
}

export function niceScale(min: number, max: number, options: Options = {}): Scale {
  const { zeroBased = false, minSpanRatio = 0.02, targetTicks = 4 } = options;
  let low = zeroBased ? Math.min(0, min) : min;
  let high = max;
  const floor = Math.max(1, Math.abs(high) * minSpanRatio);
  if (high - low < floor) {
    if (zeroBased) {
      high = low + floor;
    } else {
      const pad = (floor - (high - low)) / 2;
      low -= pad;
      high += pad;
    }
  }
  const step = niceStep((high - low) / (targetTicks - 1));
  const lower = zeroBased ? Math.min(0, Math.floor(low / step) * step) : Math.floor(low / step) * step;
  const upper = Math.ceil(high / step) * step;
  const ticks: number[] = [];
  for (let tick = lower; tick <= upper + step / 2; tick += step) ticks.push(tick);
  return { lower, upper, ticks };
}
