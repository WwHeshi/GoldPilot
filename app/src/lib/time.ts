export function formatChinaDateTime(value: string | number | Date | null | undefined) {
  if (!value) {
    return '';
  }

  const date = parseApiDate(value);

  if (Number.isNaN(date.getTime())) {
    return '';
  }

  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

function parseApiDate(value: string | number | Date) {
  if (value instanceof Date) {
    return value;
  }

  if (typeof value !== 'string') {
    return new Date(value);
  }

  const trimmed = value.trim();
  const hasTimezone = /(?:z|[+-]\d{2}:?\d{2})$/i.test(trimmed);
  const legacyDateTime = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(trimmed);

  if (!hasTimezone && legacyDateTime) {
    return parseChinaLocalDateTime(trimmed);
  }

  return new Date(trimmed);
}

function parseChinaLocalDateTime(value: string) {
  const match = value.match(
    /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$/
  );

  if (!match) {
    return new Date(value);
  }

  const [, year, month, day, hour, minute, second, fraction = '0'] = match;
  const millisecond = Number(fraction.padEnd(3, '0').slice(0, 3));

  return new Date(
    Date.UTC(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour) - 8,
      Number(minute),
      Number(second),
      millisecond
    )
  );
}
