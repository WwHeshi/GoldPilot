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
    return new Date(`${trimmed.replace(' ', 'T')}Z`);
  }

  return new Date(trimmed);
}
