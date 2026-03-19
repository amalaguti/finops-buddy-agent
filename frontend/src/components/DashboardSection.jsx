import { useState, useEffect } from 'react';
import { useProfile } from '../context/ProfileContext.jsx';
import {
  getCostsDashboardByService,
  getCostsDashboardByAccount,
  getCostsDashboardByMarketplace,
  getCostsDashboardRecommendations,
  getCostsDashboardAnomalies,
  getCostsDashboardSavingsPlans,
  getServiceAccountsForService,
  getServicesForAccount,
} from '../api/client.js';

const COLUMN_LABELS = {
  description: 'Description',
  TotalActualSpend: 'Actual spend',
  TotalExpectedSpend: 'Expected spend',
  startDate: 'Start date',
  endDate: 'End date',
  cost: 'Cost',
  value: 'Value',
};

function formatColumnHeader(key) {
  return COLUMN_LABELS[key] ?? key;
}

function isNumericColumn(key) {
  return (
    key === 'cost' ||
    key === 'value' ||
    key === 'TotalActualSpend' ||
    key === 'TotalExpectedSpend' ||
    key === 'utilization' ||
    key === 'netSavings'
  );
}

function formatMonthDay(value) {
  if (value == null || value === '') return null;
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
}

function formatCellValue(value, key) {
  if (value == null || value === '') return '—';
  if (key === 'startDate' || key === 'endDate') {
    const formatted = formatMonthDay(value);
    return formatted ?? '—';
  }
  if (key === 'utilization') {
    const n = typeof value === 'object' && value?.Amount != null ? Number(value.Amount) : Number(value);
    return Number.isFinite(n) ? `${n.toFixed(2)}%` : '—';
  }
  if (key === 'netSavings') {
    const n = typeof value === 'object' && value?.Amount != null ? Number(value.Amount) : Number(value);
    return Number.isFinite(n) ? `$${n.toFixed(2)}` : '—';
  }
  if (isNumericColumn(key)) {
    const n = typeof value === 'object' && value?.Amount != null ? Number(value.Amount) : Number(value);
    return Number.isFinite(n) ? n.toFixed(2) : String(value);
  }
  return String(value);
}

function MiniTable({ title, rows, columns, emptyMessage, keyField, onRowClick, loading }) {
  const multiColumn = Array.isArray(columns) && columns.length > 2;
  const [labelKey, valueKey] = columns;

  if (loading) {
    return (
      <div className="space-y-1">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">{title}</h4>
        <div className="flex min-h-[4rem] items-center justify-center rounded border border-finops-border bg-finops-bg-page/50 py-4">
          <div className="flex flex-col items-center gap-2">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-finops-border border-t-finops-accent" />
            <p className="text-xs text-finops-text-secondary">Loading…</p>
          </div>
        </div>
      </div>
    );
  }

  if (!rows?.length)
    return (
      <div className="space-y-1">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">{title}</h4>
        <p className="text-sm text-finops-text-secondary">{emptyMessage}</p>
      </div>
    );
  const total =
    !multiColumn && valueKey === 'cost'
      ? rows.reduce((s, r) => s + (Number(r[valueKey]) || 0), 0)
      : null;
  return (
    <div className="space-y-1">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">{title}</h4>
      <div className="overflow-x-auto rounded border border-finops-border">
        <table className="min-w-full text-xs">
          <thead className="bg-finops-btn-secondary text-left">
            <tr>
              {(multiColumn ? columns : [labelKey, valueKey]).map((col) => (
                <th
                  key={col}
                  className={
                    isNumericColumn(col)
                      ? 'px-2 py-1.5 font-medium text-finops-text-primary text-right'
                      : 'px-2 py-1.5 font-medium text-finops-text-primary'
                  }
                >
                  {multiColumn ? formatColumnHeader(col) : col === valueKey ? (valueKey === 'cost' ? 'Cost' : 'Value') : col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-finops-border">
            {rows.slice(0, 10).map((r) => (
              <tr
                key={r[keyField] ?? r[labelKey] ?? r[columns[0]] ?? Math.random()}
                onClick={onRowClick ? () => onRowClick(r) : undefined}
                className={onRowClick ? 'cursor-pointer hover:bg-finops-bg-page' : undefined}
              >
                {(multiColumn ? columns : [labelKey, valueKey]).map((col) => (
                  <td
                    key={col}
                    className={
                      isNumericColumn(col)
                        ? 'px-2 py-1.5 text-right font-mono text-finops-text-primary'
                        : 'px-2 py-1.5 text-finops-text-primary truncate max-w-[140px]'
                    }
                    title={!isNumericColumn(col) ? r[col] : undefined}
                  >
                    {formatCellValue(r[col], col)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          {total != null && !multiColumn && (
            <tfoot className="bg-finops-bg-page font-medium">
              <tr>
                <td className="px-2 py-1.5 text-finops-text-primary">Total</td>
                <td className="px-2 py-1.5 text-right font-mono text-finops-text-primary">{total.toFixed(2)}</td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}

function SavingsPlansPeriodPicker({ value, onChange }) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-xs text-finops-text-secondary">Avg over months:</span>
      {[1, 2, 3].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n)}
          className={`rounded px-2 py-0.5 text-xs font-medium ${
            value === n
              ? 'bg-finops-btn-primary text-finops-badge-text'
              : 'bg-finops-btn-secondary text-finops-text-primary hover:opacity-90'
          }`}
        >
          {n}m
        </button>
      ))}
    </div>
  );
}

function summarizeAnomalyValue(anomaly) {
  const impact = anomaly?.impact || {};
  const candidates = [
    impact.TotalImpact?.Amount,
    impact.MaxImpact?.Amount,
    impact.CurrentPeriodImpact?.TotalImpact?.Amount,
  ];
  const raw = candidates.find((v) => v != null && v !== '');
  const n = Number(raw);
  return Number.isFinite(n) ? n : 0;
}

function describeAnomaly(anomaly) {
  const label = anomaly.dimensionValue || anomaly.anomalyId || 'Anomaly';
  const start = anomaly.startDate;
  const end = anomaly.endDate;
  const score =
    anomaly.anomalyScore?.MaxScore ??
    anomaly.anomalyScore?.CurrentScore ??
    anomaly.anomalyScore?.Score;
  const parts = [label];
  if (start && end) parts.push(`${start} → ${end}`);
  if (score != null && score !== '') {
    const s = Number(score);
    parts.push(`score ${Number.isFinite(s) ? s.toFixed(1) : score}`);
  }
  return parts.join(' · ');
}

function describeRecommendation(rec) {
  const pieces = [];
  if (rec.actionType) pieces.push(rec.actionType);
  if (rec.resourceType) pieces.push(rec.resourceType);
  if (rec.accountProfile) {
    pieces.push(`acct ${rec.accountProfile}`);
  } else if (rec.accountId) {
    pieces.push(`acct ${rec.accountId}`);
  }
  return pieces.join(' · ') || rec.recommendationId || rec.id || 'Recommendation';
}

function summarizeRecommendationSavings(rec) {
  const raw = rec.estimatedMonthlySavings;
  const n = Number(raw);
  if (!Number.isFinite(n)) return null;
  return n;
}

const emptySlice = () => ({ data: null, error: null, loading: false });

export function DashboardSection() {
  const { profile, markCostsLoaded } = useProfile();
  const [savingsPlansMonths, setSavingsPlansMonths] = useState(1);
  const [byService, setByService] = useState(emptySlice);
  const [byAccount, setByAccount] = useState(emptySlice);
  const [byMarketplace, setByMarketplace] = useState(emptySlice);
  const [recommendations, setRecommendations] = useState(emptySlice);
  const [anomalies, setAnomalies] = useState(emptySlice);
  const [savingsPlans, setSavingsPlans] = useState(emptySlice);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [showSavingsPlansDetails, setShowSavingsPlansDetails] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [serviceAccounts, setServiceAccounts] = useState(null);
  const [serviceAccountsError, setServiceAccountsError] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [accountServices, setAccountServices] = useState(null);
  const [accountServicesError, setAccountServicesError] = useState(null);

  useEffect(() => {
    if (!profile) {
      setByService(emptySlice());
      setByAccount(emptySlice());
      setByMarketplace(emptySlice());
      setRecommendations(emptySlice());
      setAnomalies(emptySlice());
      setSavingsPlans(emptySlice());
      return;
    }
    const forProfile = profile;
    setByService((s) => ({ ...s, loading: true, error: null }));
    setByAccount((s) => ({ ...s, loading: true, error: null }));
    setByMarketplace((s) => ({ ...s, loading: true, error: null }));
    setRecommendations((s) => ({ ...s, loading: true, error: null }));
    setAnomalies((s) => ({ ...s, loading: true, error: null }));
    setSavingsPlans((s) => ({ ...s, loading: true, error: null }));

    let completed = 0;
    const maybeDone = () => {
      completed += 1;
      if (completed === 6) markCostsLoaded(forProfile);
    };

    getCostsDashboardByService(forProfile)
      .then((data) => setByService({ data, error: null, loading: false }))
      .catch((e) => setByService({ data: null, error: e.message, loading: false }))
      .finally(maybeDone);
    getCostsDashboardByAccount(forProfile)
      .then((data) => setByAccount({ data, error: null, loading: false }))
      .catch((e) => setByAccount({ data: null, error: e.message, loading: false }))
      .finally(maybeDone);
    getCostsDashboardByMarketplace(forProfile)
      .then((data) => setByMarketplace({ data, error: null, loading: false }))
      .catch((e) => setByMarketplace({ data: null, error: e.message, loading: false }))
      .finally(maybeDone);
    getCostsDashboardRecommendations(forProfile)
      .then((data) => setRecommendations({ data, error: null, loading: false }))
      .catch((e) => setRecommendations({ data: null, error: e.message, loading: false }))
      .finally(maybeDone);
    getCostsDashboardAnomalies(forProfile)
      .then((data) => setAnomalies({ data, error: null, loading: false }))
      .catch((e) => setAnomalies({ data: null, error: e.message, loading: false }))
      .finally(maybeDone);
    getCostsDashboardSavingsPlans(forProfile)
      .then((data) => setSavingsPlans({ data, error: null, loading: false }))
      .catch((e) => setSavingsPlans({ data: null, error: e.message, loading: false }))
      .finally(maybeDone);
  }, [profile, markCostsLoaded]);

  if (!profile) return <p className="text-sm text-finops-text-secondary">Select a profile</p>;

  const byAccountRows = (byAccount.data || []).map((row) => ({
    ...row,
    account: row.account_name || row.account_id,
  }));
  const accountNameById = new Map(byAccountRows.map((row) => [row.account_id, row.account]));
  const enrichedRecommendations = (recommendations.data || []).map((rec) => {
    const accountProfile =
      rec.accountId && accountNameById.has(rec.accountId)
        ? accountNameById.get(rec.accountId)
        : undefined;
    return { ...rec, accountProfile };
  });
  const recommendationRows = enrichedRecommendations.map((rec) => ({
    ...rec,
    description: describeRecommendation(rec),
    value: summarizeRecommendationSavings(rec),
  }));
  function impactNumber(impact, key) {
    const v = impact?.[key];
    if (v == null) return null;
    if (typeof v === 'number' && Number.isFinite(v)) return v;
    if (typeof v === 'object' && v?.Amount != null) return Number(v.Amount);
    return null;
  }
  const anomalyRows = (anomalies.data || []).map((anomaly) => {
    const impact = anomaly?.impact || {};
    return {
      ...anomaly,
      description: describeAnomaly(anomaly),
      TotalActualSpend: impactNumber(impact, 'TotalActualSpend'),
      TotalExpectedSpend: impactNumber(impact, 'TotalExpectedSpend'),
    };
  });

  const savingsPlansData = savingsPlans.data;
  const savingsPlansSummary =
    savingsPlansData?.[`savings_plans_${savingsPlansMonths}m`] ??
    savingsPlansData?.savings_plans_1m ??
    savingsPlansData?.savings_plans_2m ??
    savingsPlansData?.savings_plans_3m;
  const savingsPlansDetails =
    savingsPlansData?.[`savings_plans_details_${savingsPlansMonths}m`] ??
    savingsPlansData?.savings_plans_details_1m ??
    savingsPlansData?.savings_plans_details_2m ??
    savingsPlansData?.savings_plans_details_3m ??
    [];
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-finops-text-primary">Costs dashboard</h3>
      <p className="text-xs text-finops-text-secondary" title="Costs from the 1st of the month through today.">
        Month to date
      </p>

      <div className="grid gap-3 grid-cols-[repeat(auto-fit,minmax(220px,1fr))]">
        <MiniTable
          title="By AWS service (month to date)"
          rows={byService.error ? null : byService.data}
          columns={['service', 'cost']}
          keyField="service"
          loading={byService.loading}
          emptyMessage={byService.error ? byService.error : 'No AWS service cost data'}
          onRowClick={(row) => {
            if (!row || !row.service) return;
            setSelectedService(row.service);
            setServiceAccounts(null);
            setServiceAccountsError(null);
            if (!profile) return;
            getServiceAccountsForService(profile, row.service)
              .then((accounts) => {
                setServiceAccounts(accounts);
              })
              .catch((e) => {
                setServiceAccountsError(e.message);
              });
          }}
        />
        <MiniTable
          title="By linked account (month to date)"
          rows={byAccount.error ? null : byAccountRows}
          columns={['account', 'cost']}
          keyField="account"
          loading={byAccount.loading}
          emptyMessage={byAccount.error ? byAccount.error : 'No linked account data'}
          onRowClick={(row) => {
            if (!row || !row.account_id) return;
            setSelectedAccount(row.account_name || row.account_id);
            setAccountServices(null);
            setAccountServicesError(null);
            if (!profile) return;
            getServicesForAccount(profile, row.account_id)
              .then((services) => {
                setAccountServices(services);
              })
              .catch((e) => {
                setAccountServicesError(e.message);
              });
          }}
        />
        <MiniTable
          title="Marketplace (month to date)"
          rows={byMarketplace.error ? null : byMarketplace.data}
          columns={['product', 'cost']}
          keyField="product"
          loading={byMarketplace.loading}
          emptyMessage={byMarketplace.error ? byMarketplace.error : 'No marketplace usage this month'}
        />
        <MiniTable
          title="Optimization recommendations (top 10)"
          rows={recommendations.error ? null : recommendationRows}
          columns={['description', 'value']}
          keyField="recommendationId"
          loading={recommendations.loading}
          emptyMessage={recommendations.error ? recommendations.error : 'No optimization recommendations'}
          onRowClick={setSelectedRecommendation}
        />
        <div className="md:col-span-2">
          <MiniTable
            title="Anomalies (last 3 days)"
            rows={anomalies.error ? null : anomalyRows}
            columns={['description', 'startDate', 'endDate', 'TotalActualSpend', 'TotalExpectedSpend']}
            keyField="anomalyId"
            loading={anomalies.loading}
            emptyMessage={anomalies.error ? anomalies.error : 'No anomalies in the last 3 days'}
            onRowClick={setSelectedAnomaly}
          />
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">
              Savings Plans
            </h4>
            <SavingsPlansPeriodPicker value={savingsPlansMonths} onChange={setSavingsPlansMonths} />
          </div>
          {savingsPlans.loading ? (
            <div className="flex min-h-[4rem] items-center justify-center rounded border border-finops-border bg-finops-bg-page/50 py-4">
              <div className="flex flex-col items-center gap-2">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-finops-border border-t-finops-accent" />
                <p className="text-xs text-finops-text-secondary">Loading…</p>
              </div>
            </div>
          ) : savingsPlans.error ? (
            <p className="text-sm text-red-600">{savingsPlans.error}</p>
          ) : savingsPlansSummary ? (
            <button
              type="button"
              onClick={() => setShowSavingsPlansDetails((prev) => !prev)}
              className="w-full rounded border border-finops-border bg-finops-bg-page/50 px-2 py-2 text-left text-xs hover:border-slate-300"
            >
              <p className="text-finops-text-primary">
                Utilization:{' '}
                <strong>{Number(savingsPlansSummary.utilization_percentage ?? 0).toFixed(1)}%</strong>
              </p>
              <p className="text-finops-text-primary">
                Coverage:{' '}
                <strong>{Number(savingsPlansSummary.coverage_percentage ?? 0).toFixed(1)}%</strong>
              </p>
              <p className="text-finops-text-secondary">
                Last {savingsPlansSummary.period_months ?? 1} month(s)
              </p>
              <p className="mt-1 text-[11px] text-finops-text-secondary">
                Click for details of this period.
              </p>
            </button>
          ) : (
            <p className="text-sm text-finops-text-secondary">No Savings Plans data</p>
          )}
        </div>
      </div>
      {selectedRecommendation && (
        <div className="mt-2 rounded border border-finops-border bg-finops-bg-surface p-3 text-xs shadow-sm space-y-2">
          <div>
              <div className="mb-1 flex items-center justify-between">
                <h4 className="font-semibold text-finops-text-primary">Recommendation details</h4>
                <button
                  type="button"
                  className="text-xs text-finops-text-secondary hover:text-finops-text-primary"
                  onClick={() => setSelectedRecommendation(null)}
                >
                  Close
                </button>
              </div>
              <p className="text-finops-text-primary">{describeRecommendation(selectedRecommendation)}</p>
              <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-finops-text-secondary">
                {selectedRecommendation.resourceId != null && selectedRecommendation.resourceId !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Resource ID</dt>
                    <dd className="font-mono text-finops-text-primary break-all">{String(selectedRecommendation.resourceId)}</dd>
                  </>
                )}
                {selectedRecommendation.resourceArn != null && selectedRecommendation.resourceArn !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Resource ARN</dt>
                    <dd className="font-mono text-finops-text-primary break-all" title={selectedRecommendation.resourceArn}>
                      {String(selectedRecommendation.resourceArn)}
                    </dd>
                  </>
                )}
                {selectedRecommendation.currentResourceType != null && selectedRecommendation.currentResourceType !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Current resource type</dt>
                    <dd className="font-mono text-finops-text-primary">{String(selectedRecommendation.currentResourceType)}</dd>
                  </>
                )}
                {selectedRecommendation.recommendedResourceType != null && selectedRecommendation.recommendedResourceType !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Recommended resource type</dt>
                    <dd className="font-mono text-finops-text-primary">{String(selectedRecommendation.recommendedResourceType)}</dd>
                  </>
                )}
                {selectedRecommendation.estimatedMonthlySavings != null && selectedRecommendation.estimatedMonthlySavings !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Estimated monthly savings</dt>
                    <dd className="font-mono text-finops-text-primary font-medium">
                      {Number(selectedRecommendation.estimatedMonthlySavings).toFixed(2)}
                    </dd>
                  </>
                )}
                {selectedRecommendation.currentResourceSummary != null && selectedRecommendation.currentResourceSummary !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Current resource summary</dt>
                    <dd className="font-mono text-finops-text-primary">{String(selectedRecommendation.currentResourceSummary)}</dd>
                  </>
                )}
                {selectedRecommendation.recommendedResourceSummary != null && selectedRecommendation.recommendedResourceSummary !== '' && (
                  <>
                    <dt className="text-finops-text-secondary">Recommended resource summary</dt>
                    <dd className="font-mono text-finops-text-primary">{String(selectedRecommendation.recommendedResourceSummary)}</dd>
                  </>
                )}
                {selectedRecommendation.accountProfile && (
                  <>
                    <dt className="text-finops-text-secondary">Account</dt>
                    <dd className="font-mono text-finops-text-primary">{selectedRecommendation.accountProfile}</dd>
                  </>
                )}
              </dl>
              <details className="mt-2 border-t border-finops-border pt-2">
                <summary className="cursor-pointer text-finops-text-secondary hover:text-finops-text-primary">
                  Entire data (raw)
                </summary>
                <pre className="mt-1 max-h-64 overflow-auto rounded bg-finops-btn-secondary p-2 text-[11px] text-finops-text-primary whitespace-pre-wrap break-all">
                  {JSON.stringify(selectedRecommendation, null, 2)}
                </pre>
              </details>
          </div>
        </div>
      )}
      {selectedAccount && (
        <div className="mt-2 rounded border border-finops-border bg-finops-bg-surface p-3 text-xs shadow-sm space-y-2">
          <div className="mb-1 flex items-center justify-between">
            <h4 className="font-semibold text-finops-text-primary">
              Account details — {selectedAccount}
            </h4>
            <button
              type="button"
              className="text-xs text-finops-text-secondary hover:text-finops-text-primary"
              onClick={() => {
                setSelectedAccount(null);
                setAccountServices(null);
                setAccountServicesError(null);
              }}
            >
              Close
            </button>
          </div>
          {accountServicesError && (
            <p className="text-xs text-red-600">Details error: {accountServicesError}</p>
          )}
          {!accountServices && !accountServicesError && (
            <p className="text-xs text-finops-text-secondary">Loading service breakdown…</p>
          )}
          {accountServices && accountServices.length > 0 && (
            <MiniTable
              title="By service for this account (month to date)"
              rows={accountServices}
              columns={['service', 'cost']}
              keyField="service"
              emptyMessage="No service data for this account"
            />
          )}
          {accountServices && accountServices.length === 0 && !accountServicesError && (
            <p className="text-xs text-finops-text-secondary">No service data for this account.</p>
          )}
        </div>
      )}
      {selectedService && (
        <div className="mt-2 rounded border border-finops-border bg-finops-bg-surface p-3 text-xs shadow-sm space-y-2">
          <div className="mb-1 flex items-center justify-between">
            <h4 className="font-semibold text-finops-text-primary">
              Service details — {selectedService}
            </h4>
            <button
              type="button"
              className="text-xs text-finops-text-secondary hover:text-finops-text-primary"
              onClick={() => {
                setSelectedService(null);
                setServiceAccounts(null);
                setServiceAccountsError(null);
              }}
            >
              Close
            </button>
          </div>
          {serviceAccountsError && (
            <p className="text-xs text-red-600">Details error: {serviceAccountsError}</p>
          )}
          {!serviceAccounts && !serviceAccountsError && (
            <p className="text-xs text-finops-text-secondary">Loading account breakdown…</p>
          )}
          {serviceAccounts && serviceAccounts.length > 0 && (
            <MiniTable
              title="By linked account for this service (month to date)"
              rows={serviceAccounts.map((row) => ({
                ...row,
                account: row.account_name || row.account_id,
              }))}
              columns={['account', 'cost']}
              keyField="account_id"
              emptyMessage="No account data for this service"
            />
          )}
          {serviceAccounts && serviceAccounts.length === 0 && !serviceAccountsError && (
            <p className="text-xs text-finops-text-secondary">No account data for this service.</p>
          )}
        </div>
      )}
      {showSavingsPlansDetails && savingsPlansSummary && (
        <div className="mt-2 rounded border border-finops-border bg-finops-bg-surface p-3 text-xs shadow-sm space-y-2">
          <div className="mb-1 flex items-center justify-between">
            <h4 className="font-semibold text-finops-text-primary">Savings Plans details</h4>
            <button
              type="button"
              className="text-xs text-finops-text-secondary hover:text-finops-text-primary"
              onClick={() => setShowSavingsPlansDetails(false)}
            >
              Close
            </button>
          </div>
          <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-finops-text-secondary">
            <dt className="text-finops-text-secondary">Period</dt>
            <dd className="font-mono text-finops-text-primary">
              Last {savingsPlansSummary.period_months ?? 1} month(s)
            </dd>
            <dt className="text-finops-text-secondary">Utilization</dt>
            <dd className="font-mono text-finops-text-primary">
              {Number(savingsPlansSummary.utilization_percentage ?? 0).toFixed(2)}%
            </dd>
            <dt className="text-finops-text-secondary">Coverage</dt>
            <dd className="font-mono text-finops-text-primary">
              {Number(savingsPlansSummary.coverage_percentage ?? 0).toFixed(2)}%
            </dd>
          </dl>
          {Array.isArray(savingsPlansDetails) && savingsPlansDetails.length > 0 && (
            <div className="mt-2 space-y-1">
              <h5 className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">
                Plans in this period
              </h5>
              <MiniTable
                title=""
                rows={savingsPlansDetails.map((p) => {
                  const arn = p.savings_plan_arn || '';
                  const shortId = arn.split('/').pop() || arn.slice(-12);
                  return {
                    id: arn,
                    plan: shortId,
                    utilization: p.utilization_percentage,
                    netSavings: p.net_savings,
                  };
                })}
                columns={['plan', 'utilization', 'netSavings']}
                keyField="id"
                emptyMessage="No plans found for this period"
              />
            </div>
          )}
          <details className="mt-2 border-t border-finops-border pt-2">
            <summary className="cursor-pointer text-finops-text-secondary hover:text-finops-text-primary">
              Entire data (raw)
            </summary>
            <pre className="mt-1 max-h-64 overflow-auto rounded bg-finops-btn-secondary p-2 text-[11px] text-finops-text-primary whitespace-pre-wrap break-all">
              {JSON.stringify({ summary: savingsPlansSummary, details: savingsPlansDetails }, null, 2)}
            </pre>
          </details>
        </div>
      )}
      {selectedAnomaly && (
        <div className="mt-2 rounded border border-finops-border bg-finops-bg-surface p-3 text-xs shadow-sm space-y-2">
          <div className="mb-1 flex items-center justify-between">
            <h4 className="font-semibold text-finops-text-primary">Anomaly details</h4>
            <button
              type="button"
              className="text-xs text-finops-text-secondary hover:text-finops-text-primary"
              onClick={() => setSelectedAnomaly(null)}
            >
              Close
            </button>
          </div>
          <p className="text-finops-text-primary">{describeAnomaly(selectedAnomaly)}</p>
          {selectedAnomaly.startDate && selectedAnomaly.endDate && (
            <p className="text-finops-text-secondary">
              Interval:{' '}
              <span className="font-mono">
                {selectedAnomaly.startDate} → {selectedAnomaly.endDate}
              </span>
            </p>
          )}
          {selectedAnomaly.dimensionValue && (
            <p className="text-finops-text-secondary">
              Dimension:{' '}
              <span className="font-mono">{selectedAnomaly.dimensionValue}</span>
            </p>
          )}
          {summarizeAnomalyValue(selectedAnomaly) !== 0 && (
            <p className="text-finops-text-primary">
              Impact value:{' '}
              <strong>{summarizeAnomalyValue(selectedAnomaly).toFixed(2)}</strong>
            </p>
          )}
          <details className="mt-2 border-t border-finops-border pt-2">
            <summary className="cursor-pointer text-finops-text-secondary hover:text-finops-text-primary">
              Entire data (raw)
            </summary>
            <pre className="mt-1 max-h-64 overflow-auto rounded bg-finops-btn-secondary p-2 text-[11px] text-finops-text-primary whitespace-pre-wrap break-all">
              {JSON.stringify(selectedAnomaly, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
