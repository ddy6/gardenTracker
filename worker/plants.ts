import { getTimezoneName, type AppBindings } from "./config";

const DAY_MS = 24 * 60 * 60 * 1000;

export const STATUS_FILTER_LABELS = {
  all: "All",
  overdue: "Overdue",
  "due-soon": "Due Soon",
  good: "Good",
  "no-schedule": "No Schedule",
} as const;

export type StatusFilter = keyof typeof STATUS_FILTER_LABELS;
export type PlantStatusKey = Exclude<StatusFilter, "all">;

export interface PlantSummary {
  id: number;
  name: string;
  location: string | null;
  notes: string | null;
  watering_interval_days: number | null;
  last_watered_date: string | null;
  created_at: string | null;
  updated_at: string | null;
  location_display: string;
  last_watered_display: string;
  schedule_display: string;
  note_preview: string;
}

export interface PlantFormValues {
  name: string;
  location: string;
  notes: string;
  watering_interval_days: string;
  last_watered_date: string;
}

export interface PlantWritePayload {
  name: string;
  location: string | null;
  notes: string | null;
  watering_interval_days: number | null;
  last_watered_date: string | null;
}

export interface DashboardPlant {
  plant: PlantSummary;
  status_key: PlantStatusKey;
  status_label: string;
  next_due_date: string | null;
  next_due_display: string;
  due_hint: string;
  sort_rank: number;
}

export interface DashboardSummary {
  total_plants: number;
  overdue_count: number;
  due_soon_count: number;
  good_count: number;
  no_schedule_count: number;
}

export interface D1PlantRow {
  id: number | string;
  name: string;
  location?: string | null;
  notes?: string | null;
  watering_interval_days?: number | string | null;
  last_watered_date?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

const LIST_PLANTS_QUERY = `
SELECT
    id,
    name,
    location,
    notes,
    watering_interval_days,
    last_watered_date,
    created_at,
    updated_at
FROM plants
ORDER BY datetime(created_at) DESC, id DESC
`;

const GET_PLANT_QUERY = `
SELECT
    id,
    name,
    location,
    notes,
    watering_interval_days,
    last_watered_date,
    created_at,
    updated_at
FROM plants
WHERE id = ?
`;

const CREATE_PLANT_QUERY = `
INSERT INTO plants (
    name,
    location,
    notes,
    watering_interval_days,
    last_watered_date,
    created_at,
    updated_at
)
VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
`;

const UPDATE_PLANT_QUERY = `
UPDATE plants
SET
    name = ?,
    location = ?,
    notes = ?,
    watering_interval_days = ?,
    last_watered_date = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?
`;

const DELETE_PLANT_QUERY = `
DELETE FROM plants
WHERE id = ?
`;

const MARK_WATERED_QUERY = `
UPDATE plants
SET
    last_watered_date = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?
`;

function maybeNone(value: string | number | null | undefined): string | number | null {
  return value === undefined || value === "" ? null : value;
}

function intOrNull(value: string | number | null | undefined): number | null {
  const normalized = maybeNone(value);
  if (normalized === null) {
    return null;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function notePreview(notes: string | null): string {
  if (!notes || !notes.trim()) {
    return "No notes yet.";
  }

  const trimmed = notes.trim();
  if (trimmed.length <= 96) {
    return trimmed;
  }
  return `${trimmed.slice(0, 93).trimEnd()}...`;
}

function scheduleDisplay(interval: number | null): string {
  if (interval === null) {
    return "No schedule";
  }
  return `Every ${interval} day${interval === 1 ? "" : "s"}`;
}

export function mapPlantRow(row: D1PlantRow): PlantSummary {
  const wateringInterval = intOrNull(row.watering_interval_days);
  const location = (maybeNone(row.location) as string | null) ?? null;
  const notes = (maybeNone(row.notes) as string | null) ?? null;
  const lastWatered = (maybeNone(row.last_watered_date) as string | null) ?? null;
  const createdAt = (maybeNone(row.created_at) as string | null) ?? null;
  const updatedAt = (maybeNone(row.updated_at) as string | null) ?? null;

  return {
    id: Number(row.id),
    name: row.name,
    location,
    notes,
    watering_interval_days: wateringInterval,
    last_watered_date: lastWatered,
    created_at: createdAt,
    updated_at: updatedAt,
    location_display: location || "Unassigned",
    last_watered_display: lastWatered || "Never",
    schedule_display: scheduleDisplay(wateringInterval),
    note_preview: notePreview(notes),
  };
}

async function execute(env: AppBindings, statement: string, ...params: Array<string | number | null>): Promise<D1Result> {
  let prepared = env.DB.prepare(statement);
  if (params.length > 0) {
    prepared = prepared.bind(...params);
  }
  return prepared.run();
}

export async function listPlants(env: AppBindings): Promise<PlantSummary[]> {
  const result = await env.DB.prepare(LIST_PLANTS_QUERY).all<D1PlantRow>();
  return (result.results || []).map(mapPlantRow);
}

export async function getPlant(env: AppBindings, plantId: number): Promise<PlantSummary | null> {
  const row = await env.DB.prepare(GET_PLANT_QUERY).bind(plantId).first<D1PlantRow>();
  return row ? mapPlantRow(row) : null;
}

export async function createPlant(env: AppBindings, payload: PlantWritePayload): Promise<void> {
  await execute(
    env,
    CREATE_PLANT_QUERY,
    payload.name,
    payload.location,
    payload.notes,
    payload.watering_interval_days,
    payload.last_watered_date,
  );
}

export async function updatePlant(env: AppBindings, plantId: number, payload: PlantWritePayload): Promise<void> {
  await execute(
    env,
    UPDATE_PLANT_QUERY,
    payload.name,
    payload.location,
    payload.notes,
    payload.watering_interval_days,
    payload.last_watered_date,
    plantId,
  );
}

export async function deletePlant(env: AppBindings, plantId: number): Promise<void> {
  await execute(env, DELETE_PLANT_QUERY, plantId);
}

export async function markPlantWatered(env: AppBindings, plantId: number, wateredOn: string): Promise<void> {
  await execute(env, MARK_WATERED_QUERY, wateredOn, plantId);
}

function readStringField(
  formData: Record<string, string | File | (string | File)[]>,
  key: string,
): string {
  const rawValue = formData[key];
  const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
  return typeof value === "string" ? value.trim() : "";
}

export function emptyPlantFormValues(): PlantFormValues {
  return {
    name: "",
    location: "",
    notes: "",
    watering_interval_days: "",
    last_watered_date: "",
  };
}

export function plantFormValuesFromPlant(plant: PlantSummary): PlantFormValues {
  return {
    name: plant.name,
    location: plant.location || "",
    notes: plant.notes || "",
    watering_interval_days: plant.watering_interval_days === null ? "" : String(plant.watering_interval_days),
    last_watered_date: plant.last_watered_date || "",
  };
}

export function parsePlantFormValues(
  formData: Record<string, string | File | (string | File)[]>,
): PlantFormValues {
  return {
    name: readStringField(formData, "name"),
    location: readStringField(formData, "location"),
    notes: readStringField(formData, "notes"),
    watering_interval_days: readStringField(formData, "watering_interval_days"),
    last_watered_date: readStringField(formData, "last_watered_date"),
  };
}

function isValidIsoDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return false;
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const candidate = new Date(Date.UTC(year, month - 1, day));
  return (
    candidate.getUTCFullYear() === year &&
    candidate.getUTCMonth() === month - 1 &&
    candidate.getUTCDate() === day
  );
}

export function validatePlantForm(values: PlantFormValues): {
  payload: PlantWritePayload | null;
  errors: Record<string, string>;
} {
  const errors: Record<string, string> = {};

  const name = values.name.trim();
  if (!name) {
    errors.name = "Plant name is required.";
  }

  let wateringIntervalDays: number | null = null;
  if (values.watering_interval_days) {
    if (!/^-?\d+$/.test(values.watering_interval_days)) {
      errors.watering_interval_days = "Watering interval must be a whole number.";
    } else {
      wateringIntervalDays = Number.parseInt(values.watering_interval_days, 10);
      if (wateringIntervalDays <= 0) {
        errors.watering_interval_days = "Watering interval must be greater than zero.";
      }
    }
  }

  const lastWateredDate = values.last_watered_date || null;
  if (lastWateredDate && !isValidIsoDate(lastWateredDate)) {
    errors.last_watered_date = "Last watered date must use YYYY-MM-DD.";
  }

  if (Object.keys(errors).length > 0) {
    return { payload: null, errors };
  }

  return {
    payload: {
      name,
      location: values.location || null,
      notes: values.notes || null,
      watering_interval_days: wateringIntervalDays,
      last_watered_date: lastWateredDate,
    },
    errors: {},
  };
}

function parseIsoDate(value: string | null): Date | null {
  if (!value) {
    return null;
  }

  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return null;
  }

  return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
}

function formatIsoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function addDays(value: Date, days: number): Date {
  return new Date(value.getTime() + days * DAY_MS);
}

function daysBetween(later: Date, earlier: Date): number {
  return Math.round((later.getTime() - earlier.getTime()) / DAY_MS);
}

function formatDueDate(value: Date | null, today: Date): string {
  if (value === null) {
    return "No schedule";
  }

  const isoDate = formatIsoDate(value);
  if (isoDate === formatIsoDate(today)) {
    return "Today";
  }
  if (isoDate === formatIsoDate(addDays(today, 1))) {
    return "Tomorrow";
  }
  return isoDate;
}

function formatDueHint(nextDueDate: Date | null, today: Date, hasSchedule: boolean): string {
  if (!hasSchedule) {
    return "Set a watering interval to track due dates.";
  }
  if (nextDueDate === null) {
    return "Needs a last watered date.";
  }

  const deltaDays = daysBetween(nextDueDate, today);
  if (deltaDays < 0) {
    const overdueDays = Math.abs(deltaDays);
    return `Overdue by ${overdueDays} day${overdueDays === 1 ? "" : "s"}.`;
  }
  if (deltaDays === 0) {
    return "Due today.";
  }
  if (deltaDays === 1) {
    return "Due tomorrow.";
  }
  return `Due in ${deltaDays} days.`;
}

export function getToday(env: AppBindings): Date {
  try {
    const formatter = new Intl.DateTimeFormat("en-CA", {
      timeZone: getTimezoneName(env),
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    const parts = formatter.formatToParts(new Date());
    const year = Number(parts.find((part) => part.type === "year")?.value);
    const month = Number(parts.find((part) => part.type === "month")?.value);
    const day = Number(parts.find((part) => part.type === "day")?.value);
    return new Date(Date.UTC(year, month - 1, day));
  } catch {
    const now = new Date();
    return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  }
}

export function normalizeStatusFilter(value: string | undefined): StatusFilter {
  if (value && value in STATUS_FILTER_LABELS) {
    return value as StatusFilter;
  }
  return "all";
}

function buildDashboardPlant(plant: PlantSummary, today: Date): DashboardPlant {
  let statusKey: PlantStatusKey;
  let nextDueDate: Date | null;

  if (plant.watering_interval_days === null) {
    statusKey = "no-schedule";
    nextDueDate = null;
  } else {
    const lastWateredDate = parseIsoDate(plant.last_watered_date);
    if (lastWateredDate === null) {
      nextDueDate = today;
    } else {
      nextDueDate = addDays(lastWateredDate, plant.watering_interval_days);
    }

    const daysUntilDue = daysBetween(nextDueDate, today);
    if (daysUntilDue < 0) {
      statusKey = "overdue";
    } else if (daysUntilDue <= 2) {
      statusKey = "due-soon";
    } else {
      statusKey = "good";
    }
  }

  const statusLabelMap: Record<PlantStatusKey, string> = {
    overdue: "Overdue",
    "due-soon": "Due soon",
    good: "Good",
    "no-schedule": "No schedule",
  };

  const sortOrder: Record<PlantStatusKey, number> = {
    overdue: 0,
    "due-soon": 1,
    good: 2,
    "no-schedule": 3,
  };

  return {
    plant,
    status_key: statusKey,
    status_label: statusLabelMap[statusKey],
    next_due_date: nextDueDate ? formatIsoDate(nextDueDate) : null,
    next_due_display: formatDueDate(nextDueDate, today),
    due_hint: formatDueHint(nextDueDate, today, plant.watering_interval_days !== null),
    sort_rank: sortOrder[statusKey],
  };
}

export function buildDashboardPlants(plants: PlantSummary[], today: Date): DashboardPlant[] {
  return plants
    .map((plant) => buildDashboardPlant(plant, today))
    .sort((left, right) => {
      if (left.sort_rank !== right.sort_rank) {
        return left.sort_rank - right.sort_rank;
      }

      const leftDue = left.next_due_date ?? "9999-12-31";
      const rightDue = right.next_due_date ?? "9999-12-31";
      if (leftDue !== rightDue) {
        return leftDue.localeCompare(rightDue);
      }

      const nameCompare = left.plant.name.toLowerCase().localeCompare(right.plant.name.toLowerCase());
      if (nameCompare !== 0) {
        return nameCompare;
      }

      return left.plant.id - right.plant.id;
    });
}

export function filterDashboardPlants(
  dashboardPlants: DashboardPlant[],
  statusFilter: StatusFilter,
): DashboardPlant[] {
  if (statusFilter === "all") {
    return dashboardPlants;
  }
  return dashboardPlants.filter((item) => item.status_key === statusFilter);
}

export function buildDashboardSummary(dashboardPlants: DashboardPlant[]): DashboardSummary {
  const overdueCount = dashboardPlants.filter((item) => item.status_key === "overdue").length;
  const dueSoonCount = dashboardPlants.filter((item) => item.status_key === "due-soon").length;
  const goodCount = dashboardPlants.filter((item) => item.status_key === "good").length;
  const noScheduleCount = dashboardPlants.filter((item) => item.status_key === "no-schedule").length;

  return {
    total_plants: dashboardPlants.length,
    overdue_count: overdueCount,
    due_soon_count: dueSoonCount,
    good_count: goodCount,
    no_schedule_count: noScheduleCount,
  };
}

export async function pingDatabase(env: AppBindings): Promise<{ ok: boolean; error: string | null }> {
  try {
    await env.DB.prepare("SELECT 1 AS ok").first();
    return { ok: true, error: null };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
