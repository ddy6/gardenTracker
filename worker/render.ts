import { APP_NAME, CSRF_FORM_FIELD_NAME } from "./config.ts";
import type {
  DashboardPlant,
  DashboardSummary,
  PlantFormValues,
  PlantSummary,
  StatusFilter,
} from "./plants.ts";

interface DashboardFilterOption {
  key: StatusFilter;
  label: string;
  count: number;
  isActive: boolean;
  url: string;
}

interface DashboardPageData extends DashboardSummary {
  csrfToken: string;
  dashboardPlants: DashboardPlant[];
  noticeMessage: string | null;
  activeStatusFilter: StatusFilter;
  activeStatusLabel: string;
  statusFilters: DashboardFilterOption[];
  visiblePlantsCount: number;
  newPlantUrl: string;
}

interface PlantFormPageData {
  csrfToken: string;
  pageTitle: string;
  formTitle: string;
  submitLabel: string;
  formAction: string;
  formValues: PlantFormValues;
  errors: Record<string, string>;
  backUrl: string;
}

interface ErrorPageData {
  pageTitle: string;
  errorTitle: string;
  errorMessage: string;
  backUrl: string;
  backLabel: string;
}

interface LoginPageData {
  csrfToken: string;
  errorMessage: string | null;
}

function escapeHtml(value: unknown): string {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function pageTitle(pageTitleText?: string): string {
  return pageTitleText ? `${escapeHtml(pageTitleText)} | ${escapeHtml(APP_NAME)}` : escapeHtml(APP_NAME);
}

function layout(content: string, pageTitleText?: string): string {
  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${pageTitle(pageTitleText)}</title>
    <link rel="stylesheet" href="/styles.css">
  </head>
  <body>
    <main class="shell">
      ${content}
    </main>
  </body>
</html>`;
}

function csrfField(csrfToken: string): string {
  return `<input type="hidden" name="${escapeHtml(CSRF_FORM_FIELD_NAME)}" value="${escapeHtml(csrfToken)}">`;
}

function errorLine(errors: Record<string, string>, key: string): string {
  if (!errors[key]) {
    return "";
  }
  return `<span class="field-error">${escapeHtml(errors[key])}</span>`;
}

export function withQuery(path: string, params: Record<string, string | null | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return queryString ? `${path}?${queryString}` : path;
}

export function renderLoginPage(data: LoginPageData): string {
  const errorMessage = data.errorMessage
    ? `<p class="flash flash-error">${escapeHtml(data.errorMessage)}</p>`
    : "";

  return layout(
    `<section class="panel auth-panel">
      <p class="eyebrow">Garden Dashboard</p>
      <h1>${escapeHtml(APP_NAME)}</h1>
      <p class="lede">Enter the shared password to open the private garden dashboard.</p>
      ${errorMessage}
      <form method="post" action="/login" class="stack">
        ${csrfField(data.csrfToken)}
        <label class="field">
          <span>Password</span>
          <input type="password" name="password" autocomplete="current-password" required>
        </label>
        <button type="submit">Enter Dashboard</button>
      </form>
    </section>`,
  );
}

function renderPlantCard(item: DashboardPlant, csrfToken: string, activeStatusFilter: StatusFilter): string {
  const statusQuery = activeStatusFilter === "all" ? null : activeStatusFilter;
  const waterAction = withQuery(`/plants/${item.plant.id}/water`, { status: statusQuery });
  const editUrl = withQuery(`/plants/${item.plant.id}/edit`, { status: statusQuery });
  const deleteAction = withQuery(`/plants/${item.plant.id}/delete`, { status: statusQuery });

  return `<article class="plant-card">
    <div class="plant-heading">
      <div>
        <h2>${escapeHtml(item.plant.name)}</h2>
        <p class="plant-location">${escapeHtml(item.plant.location_display)}</p>
      </div>
      <div class="plant-badges">
        <span class="plant-status plant-status-${escapeHtml(item.status_key)}">${escapeHtml(item.status_label)}</span>
        <span class="plant-schedule">${escapeHtml(item.plant.schedule_display)}</span>
      </div>
    </div>
    <p class="plant-notes">${escapeHtml(item.plant.note_preview)}</p>
    <div class="plant-meta">
      <span>Last watered: ${escapeHtml(item.plant.last_watered_display)}</span>
      <span>Next due: ${escapeHtml(item.next_due_display)}</span>
      <span>${escapeHtml(item.due_hint)}</span>
      <span>Record #${escapeHtml(item.plant.id)}</span>
    </div>
    <div class="plant-actions">
      <form method="post" action="${escapeHtml(waterAction)}">
        ${csrfField(csrfToken)}
        <button type="submit">Mark watered</button>
      </form>
      <a href="${escapeHtml(editUrl)}" class="button-link button-link-secondary">Edit</a>
      <form method="post" action="${escapeHtml(deleteAction)}">
        ${csrfField(csrfToken)}
        <button type="submit" class="danger">Delete</button>
      </form>
    </div>
  </article>`;
}

export function renderDashboardPage(data: DashboardPageData): string {
  const noticeMessage = data.noticeMessage
    ? `<p class="flash flash-success">${escapeHtml(data.noticeMessage)}</p>`
    : "";
  const noScheduleNote = data.no_schedule_count
    ? `<p class="subtle-note">${escapeHtml(data.no_schedule_count)} plant${data.no_schedule_count === 1 ? "" : "s"} still need${data.no_schedule_count === 1 ? "s" : ""} a watering interval to join the schedule.</p>`
    : "";
  const filterNote =
    data.activeStatusFilter !== "all"
      ? `<p class="subtle-note">Showing ${escapeHtml(data.visiblePlantsCount)} ${escapeHtml(
          data.activeStatusLabel.toLowerCase(),
        )} plant${data.visiblePlantsCount === 1 ? "" : "s"} out of ${escapeHtml(data.total_plants)} total.</p>`
      : "";
  const filterLinks = data.statusFilters
    .map(
      (filterOption) => `<a href="${escapeHtml(filterOption.url)}" class="filter-chip${
        filterOption.isActive ? " filter-chip-active" : ""
      }">
        <span>${escapeHtml(filterOption.label)}</span>
        <span class="filter-count">${escapeHtml(filterOption.count)}</span>
      </a>`,
    )
    .join("");

  let plantSection = "";
  if (data.dashboardPlants.length > 0) {
    plantSection = `<section class="plant-list" aria-label="Plants">
      ${data.dashboardPlants.map((item) => renderPlantCard(item, data.csrfToken, data.activeStatusFilter)).join("")}
    </section>`;
  } else if (data.total_plants > 0) {
    plantSection = `<section class="empty-state">
      <h2>No plants match this filter</h2>
      <p>Try another status filter to see the rest of the garden.</p>
      <div class="empty-actions">
        <a href="/" class="button-link">Show all plants</a>
      </div>
    </section>`;
  } else {
    plantSection = `<section class="empty-state">
      <h2>No plants yet</h2>
      <p>The watering dashboard is ready. Add the first plant to start tracking what needs attention.</p>
      <div class="empty-actions">
        <a href="${escapeHtml(data.newPlantUrl)}" class="button-link">Add the first plant</a>
      </div>
    </section>`;
  }

  return layout(
    `<section class="panel dashboard-panel">
      <div class="hero">
        <div>
          <p class="eyebrow">Garden Dashboard</p>
          <h1>Plant Overview</h1>
          <p class="lede">Plants are now sorted by what needs attention first, with one-click watering updates from the dashboard.</p>
        </div>
        <div class="hero-actions">
          <a href="${escapeHtml(data.newPlantUrl)}" class="button-link">Add plant</a>
          <form method="post" action="/logout">
            ${csrfField(data.csrfToken)}
            <button type="submit" class="secondary">Log out</button>
          </form>
        </div>
      </div>

      ${noticeMessage}

      <div class="status-grid">
        <article class="status-card">
          <p class="status-label">Total plants</p>
          <p class="status-value">${escapeHtml(data.total_plants)}</p>
          <p class="status-meta">All entries currently stored in D1.</p>
        </article>

        <article class="status-card">
          <p class="status-label">Overdue</p>
          <p class="status-value error">${escapeHtml(data.overdue_count)}</p>
          <p class="status-meta">Plants that should already have been watered.</p>
        </article>

        <article class="status-card">
          <p class="status-label">Due soon</p>
          <p class="status-value success">${escapeHtml(data.due_soon_count)}</p>
          <p class="status-meta">Plants due today, within the next two days, or still missing a first watering date.</p>
        </article>
      </div>

      ${noScheduleNote}

      <nav class="filter-row" aria-label="Status filters">
        ${filterLinks}
      </nav>

      ${filterNote}

      ${plantSection}
    </section>`,
    "Plant Overview",
  );
}

export function renderPlantFormPage(data: PlantFormPageData): string {
  return layout(
    `<section class="panel form-panel">
      <div class="hero">
        <div>
          <p class="eyebrow">Garden Dashboard</p>
          <h1>${escapeHtml(data.formTitle)}</h1>
          <p class="lede">Capture the core details and watering schedule so the dashboard can flag what needs attention.</p>
        </div>
        <a href="${escapeHtml(data.backUrl)}" class="button-link button-link-secondary">Back to dashboard</a>
      </div>

      <form method="post" action="${escapeHtml(data.formAction)}" class="stack">
        ${csrfField(data.csrfToken)}
        <div class="form-grid">
          <label class="field">
            <span>Plant name</span>
            <input type="text" name="name" value="${escapeHtml(data.formValues.name)}" required>
            ${errorLine(data.errors, "name")}
          </label>

          <label class="field">
            <span>Location</span>
            <input type="text" name="location" value="${escapeHtml(data.formValues.location)}" placeholder="Bed A, porch, kitchen window">
          </label>

          <label class="field">
            <span>Watering interval (days)</span>
            <input type="number" min="1" step="1" name="watering_interval_days" value="${escapeHtml(
              data.formValues.watering_interval_days,
            )}" placeholder="3">
            ${errorLine(data.errors, "watering_interval_days")}
          </label>

          <label class="field">
            <span>Last watered</span>
            <input type="date" name="last_watered_date" value="${escapeHtml(data.formValues.last_watered_date)}">
            ${errorLine(data.errors, "last_watered_date")}
          </label>
        </div>

        <label class="field">
          <span>Notes</span>
          <textarea name="notes" rows="6" placeholder="Seed source, pruning notes, or anything worth remembering.">${escapeHtml(
            data.formValues.notes,
          )}</textarea>
        </label>

        <div class="form-actions">
          <button type="submit">${escapeHtml(data.submitLabel)}</button>
          <a href="${escapeHtml(data.backUrl)}" class="button-link button-link-secondary">Cancel</a>
        </div>
      </form>
    </section>`,
    data.pageTitle,
  );
}

export function renderErrorPage(data: ErrorPageData): string {
  return layout(
    `<section class="panel auth-panel">
      <p class="eyebrow">Garden Dashboard</p>
      <h1>${escapeHtml(data.errorTitle)}</h1>
      <p class="lede">${escapeHtml(data.errorMessage)}</p>
      <div class="empty-actions">
        <a href="${escapeHtml(data.backUrl)}" class="button-link">${escapeHtml(data.backLabel)}</a>
      </div>
    </section>`,
    data.pageTitle,
  );
}

export function dashboardNoticeMessage(notice: string | undefined): string | null {
  const notices: Record<string, string> = {
    created: "Plant added.",
    updated: "Plant updated.",
    deleted: "Plant deleted.",
    watered: "Plant marked as watered.",
  };
  return notice ? notices[notice] || null : null;
}

export type { DashboardFilterOption, DashboardPageData, ErrorPageData, LoginPageData, PlantFormPageData, PlantSummary };
