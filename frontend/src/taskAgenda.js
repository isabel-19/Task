// Use local calendar dates so UTC offsets cannot shift a deadline to yesterday.
export function dayKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export function weekStart(value = new Date()) {
  const date = new Date(value.getFullYear(), value.getMonth(), value.getDate(), 12);
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  return date;
}
export function shiftDay(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
}
export function weekDays(start) {
  return Array.from({ length: 7 }, (_, index) => {
    const date = shiftDay(start, index);
    return {
      key: dayKey(date),
      label: date.toLocaleDateString('es-PE', { weekday: 'long', day: 'numeric', month: 'short' }),
    };
  });
}
