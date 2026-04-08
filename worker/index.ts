import { Hono, type Context } from "hono";

import {
  applyAnonymousCsrfCookie,
  clearSessionCookies,
  getCsrfTokenForRequest,
  requestHasValidCsrfToken,
  requestIsAuthenticated,
  setAuthCookieOnContext,
} from "./auth";
import { CSRF_FORM_FIELD_NAME, type AppEnv } from "./config";
import {
  buildDashboardPlants,
  buildDashboardSummary,
  createPlant,
  deletePlant,
  emptyPlantFormValues,
  filterDashboardPlants,
  getPlant,
  getToday,
  listPlants,
  markPlantWatered,
  normalizeStatusFilter,
  parsePlantFormValues,
  pingDatabase,
  plantFormValuesFromPlant,
  STATUS_FILTER_LABELS,
  updatePlant,
  validatePlantForm,
} from "./plants";
import {
  dashboardNoticeMessage,
  renderDashboardPage,
  renderErrorPage,
  renderLoginPage,
  renderPlantFormPage,
  withQuery,
} from "./render";

const app = new Hono<AppEnv>();
type AppContext = Context<AppEnv>;

function redirectStatusFilter(rawValue: string | undefined): string | null {
  const statusFilter = normalizeStatusFilter(rawValue);
  return statusFilter === "all" ? null : statusFilter;
}

function submittedField(
  formData: Record<string, string | File | (string | File)[]>,
  key: string,
): string {
  const rawValue = formData[key];
  const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
  return typeof value === "string" ? value : "";
}

async function requireAuthentication(c: AppContext): Promise<Response | null> {
  if (!(await requestIsAuthenticated(c))) {
    return c.redirect("/login", 303);
  }
  return null;
}

async function renderLogin(c: AppContext, errorMessage: string | null, status: 200 | 401 = 200): Promise<Response> {
  const csrfToken = await getCsrfTokenForRequest(c);
  const isAuthenticated = await requestIsAuthenticated(c);
  applyAnonymousCsrfCookie(c, csrfToken, isAuthenticated);
  return c.html(renderLoginPage({ csrfToken, errorMessage }), status);
}

async function renderDashboard(c: AppContext): Promise<Response> {
  const env = c.env;
  const today = getToday(env);
  const plants = await listPlants(env);
  const dashboardPlants = buildDashboardPlants(plants, today);
  const summary = buildDashboardSummary(dashboardPlants);
  const activeStatusFilter = normalizeStatusFilter(c.req.query("status"));
  const visibleDashboardPlants = filterDashboardPlants(dashboardPlants, activeStatusFilter);
  const filterCounts = {
    all: summary.total_plants,
    overdue: summary.overdue_count,
    "due-soon": summary.due_soon_count,
    good: summary.good_count,
    "no-schedule": summary.no_schedule_count,
  };
  const statusFilters = (Object.keys(STATUS_FILTER_LABELS) as Array<keyof typeof STATUS_FILTER_LABELS>).map((key) => ({
    key,
    label: STATUS_FILTER_LABELS[key],
    count: filterCounts[key],
    isActive: key === activeStatusFilter,
    url: withQuery("/", { status: key === "all" ? null : key }),
  }));
  const csrfToken = await getCsrfTokenForRequest(c);

  return c.html(
    renderDashboardPage({
      csrfToken,
      dashboardPlants: visibleDashboardPlants,
      noticeMessage: dashboardNoticeMessage(c.req.query("notice")),
      activeStatusFilter,
      activeStatusLabel: STATUS_FILTER_LABELS[activeStatusFilter],
      statusFilters,
      visiblePlantsCount: visibleDashboardPlants.length,
      newPlantUrl: withQuery("/plants/new", {
        status: activeStatusFilter === "all" ? null : activeStatusFilter,
      }),
      ...summary,
    }),
  );
}

async function renderPlantForm(
  c: AppContext,
  {
    pageTitle,
    formTitle,
    submitLabel,
    formAction,
    formValues,
    errors,
    backUrl,
    status,
  }: {
    pageTitle: string;
    formTitle: string;
    submitLabel: string;
    formAction: string;
    formValues: ReturnType<typeof emptyPlantFormValues>;
    errors?: Record<string, string>;
    backUrl: string;
    status?: 200 | 400;
  },
): Promise<Response> {
  const csrfToken = await getCsrfTokenForRequest(c);
  return c.html(
    renderPlantFormPage({
      csrfToken,
      pageTitle,
      formTitle,
      submitLabel,
      formAction,
      formValues,
      errors: errors || {},
      backUrl,
    }),
    status || 200,
  );
}

async function renderInvalidForm(
  c: AppContext,
  data: {
    errorTitle: string;
    errorMessage: string;
    backUrl: string;
    backLabel: string;
    pageTitle: string;
    status: 403;
  },
): Promise<Response> {
  const csrfToken = await getCsrfTokenForRequest(c);
  const isAuthenticated = await requestIsAuthenticated(c);
  applyAnonymousCsrfCookie(c, csrfToken, isAuthenticated);
  return c.html(
    renderErrorPage({
      pageTitle: data.pageTitle,
      errorTitle: data.errorTitle,
      errorMessage: data.errorMessage,
      backUrl: data.backUrl,
      backLabel: data.backLabel,
    }),
    data.status,
  );
}

app.get("/healthz", (c) => c.json({ ok: true }));

app.get("/login", async (c) => {
  if (await requestIsAuthenticated(c)) {
    return c.redirect("/", 303);
  }
  return renderLogin(c, null);
});

app.post("/login", async (c) => {
  const formData = await c.req.parseBody();
  const submittedCsrfToken = submittedField(formData, CSRF_FORM_FIELD_NAME);
  if (!(await requestHasValidCsrfToken(c, submittedCsrfToken))) {
    return renderInvalidForm(c, {
      errorTitle: "Refresh Required",
      errorMessage: "The login form expired. Reload the page and try again.",
      backUrl: "/login",
      backLabel: "Back to login",
      pageTitle: "Invalid Form Submission",
      status: 403,
    });
  }

  const submittedPassword = submittedField(formData, "password");
  if (!c.env.APP_PASSWORD || submittedPassword !== c.env.APP_PASSWORD) {
    return renderLogin(c, "Incorrect password. Try again.", 401);
  }

  await setAuthCookieOnContext(c);
  return c.redirect("/", 303);
});

app.post("/logout", async (c) => {
  const formData = await c.req.parseBody();
  const submittedCsrfToken = submittedField(formData, CSRF_FORM_FIELD_NAME);
  if (!(await requestHasValidCsrfToken(c, submittedCsrfToken))) {
    return renderInvalidForm(c, {
      errorTitle: "Refresh Required",
      errorMessage: "The logout form expired. Reload the dashboard and try again.",
      backUrl: "/",
      backLabel: "Back to dashboard",
      pageTitle: "Invalid Form Submission",
      status: 403,
    });
  }

  clearSessionCookies(c);
  return c.redirect("/login", 303);
});

app.get("/", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }
  return renderDashboard(c);
});

app.get("/plants/new", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }

  const statusFilter = redirectStatusFilter(c.req.query("status"));
  return renderPlantForm(c, {
    pageTitle: "Add Plant",
    formTitle: "Add Plant",
    submitLabel: "Save plant",
    formAction: withQuery("/plants/new", { status: statusFilter }),
    formValues: emptyPlantFormValues(),
    backUrl: withQuery("/", { status: statusFilter }),
  });
});

app.post("/plants/new", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }

  const statusFilter = redirectStatusFilter(c.req.query("status"));
  const formData = await c.req.parseBody();
  const submittedCsrfToken = submittedField(formData, CSRF_FORM_FIELD_NAME);
  if (!(await requestHasValidCsrfToken(c, submittedCsrfToken))) {
    return renderInvalidForm(c, {
      errorTitle: "Refresh Required",
      errorMessage: "This form is no longer valid. Reload the page and try again.",
      backUrl: withQuery("/plants/new", { status: statusFilter }),
      backLabel: "Back to add plant",
      pageTitle: "Invalid Form Submission",
      status: 403,
    });
  }

  const formValues = parsePlantFormValues(formData);
  const { payload, errors } = validatePlantForm(formValues);
  if (!payload) {
    return renderPlantForm(c, {
      pageTitle: "Add Plant",
      formTitle: "Add Plant",
      submitLabel: "Save plant",
      formAction: withQuery("/plants/new", { status: statusFilter }),
      formValues,
      errors,
      backUrl: withQuery("/", { status: statusFilter }),
      status: 400,
    });
  }

  await createPlant(c.env, payload);
  return c.redirect(withQuery("/", { notice: "created", status: statusFilter }), 303);
});

app.get("/plants/:plantId/edit", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }

  const plant = await getPlant(c.env, Number(c.req.param("plantId")));
  if (!plant) {
    return c.notFound();
  }

  const statusFilter = redirectStatusFilter(c.req.query("status"));
  return renderPlantForm(c, {
    pageTitle: `Edit ${plant.name}`,
    formTitle: `Edit ${plant.name}`,
    submitLabel: "Save changes",
    formAction: withQuery(`/plants/${plant.id}/edit`, { status: statusFilter }),
    formValues: plantFormValuesFromPlant(plant),
    backUrl: withQuery("/", { status: statusFilter }),
  });
});

app.post("/plants/:plantId/edit", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }

  const plantId = Number(c.req.param("plantId"));
  const existingPlant = await getPlant(c.env, plantId);
  if (!existingPlant) {
    return c.notFound();
  }

  const statusFilter = redirectStatusFilter(c.req.query("status"));
  const formData = await c.req.parseBody();
  const submittedCsrfToken = submittedField(formData, CSRF_FORM_FIELD_NAME);
  if (!(await requestHasValidCsrfToken(c, submittedCsrfToken))) {
    return renderInvalidForm(c, {
      errorTitle: "Refresh Required",
      errorMessage: "This form is no longer valid. Reload the page and try again.",
      backUrl: withQuery(`/plants/${plantId}/edit`, { status: statusFilter }),
      backLabel: "Back to edit plant",
      pageTitle: "Invalid Form Submission",
      status: 403,
    });
  }

  const formValues = parsePlantFormValues(formData);
  const { payload, errors } = validatePlantForm(formValues);
  if (!payload) {
    return renderPlantForm(c, {
      pageTitle: `Edit ${existingPlant.name}`,
      formTitle: `Edit ${existingPlant.name}`,
      submitLabel: "Save changes",
      formAction: withQuery(`/plants/${plantId}/edit`, { status: statusFilter }),
      formValues,
      errors,
      backUrl: withQuery("/", { status: statusFilter }),
      status: 400,
    });
  }

  await updatePlant(c.env, plantId, payload);
  return c.redirect(withQuery("/", { notice: "updated", status: statusFilter }), 303);
});

app.post("/plants/:plantId/delete", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }

  const plantId = Number(c.req.param("plantId"));
  const plant = await getPlant(c.env, plantId);
  if (!plant) {
    return c.notFound();
  }

  const statusFilter = redirectStatusFilter(c.req.query("status"));
  const formData = await c.req.parseBody();
  const submittedCsrfToken = submittedField(formData, CSRF_FORM_FIELD_NAME);
  if (!(await requestHasValidCsrfToken(c, submittedCsrfToken))) {
    return renderInvalidForm(c, {
      errorTitle: "Refresh Required",
      errorMessage: "This form is no longer valid. Reload the page and try again.",
      backUrl: withQuery("/", { status: statusFilter }),
      backLabel: "Back to dashboard",
      pageTitle: "Invalid Form Submission",
      status: 403,
    });
  }

  await deletePlant(c.env, plantId);
  return c.redirect(withQuery("/", { notice: "deleted", status: statusFilter }), 303);
});

app.post("/plants/:plantId/water", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return unauthorized;
  }

  const plantId = Number(c.req.param("plantId"));
  const plant = await getPlant(c.env, plantId);
  if (!plant) {
    return c.notFound();
  }

  const statusFilter = redirectStatusFilter(c.req.query("status"));
  const formData = await c.req.parseBody();
  const submittedCsrfToken = submittedField(formData, CSRF_FORM_FIELD_NAME);
  if (!(await requestHasValidCsrfToken(c, submittedCsrfToken))) {
    return renderInvalidForm(c, {
      errorTitle: "Refresh Required",
      errorMessage: "This form is no longer valid. Reload the page and try again.",
      backUrl: withQuery("/", { status: statusFilter }),
      backLabel: "Back to dashboard",
      pageTitle: "Invalid Form Submission",
      status: 403,
    });
  }

  await markPlantWatered(c.env, plantId, getToday(c.env).toISOString().slice(0, 10));
  return c.redirect(withQuery("/", { notice: "watered", status: statusFilter }), 303);
});

app.get("/debug/d1", async (c) => {
  const unauthorized = await requireAuthentication(c);
  if (unauthorized) {
    return c.json({ ok: false, error: "Unauthorized" }, 401);
  }

  const result = await pingDatabase(c.env);
  return c.json(result, result.ok ? 200 : 500);
});

export default app;
