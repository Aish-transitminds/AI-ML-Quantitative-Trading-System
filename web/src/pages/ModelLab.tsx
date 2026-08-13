import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../stores/useStore';
import FeatureImportanceChart from '../components/charts/FeatureImportanceChart';
import { formatPercent } from '../utils/formatters';
import { api } from '../api/client';
import confetti from 'canvas-confetti';
import { toast } from 'sonner';

export default function ModelLab() {
  const { modelResults, bestModel, datasetInfo, featureImportance, thresholdAnalysis, fetchModels } = useStore();
  const [retraining, setRetraining] = useState(false);

  useEffect(() => { fetchModels(); }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    const toastId = toast.loading('Training models in background...', {
      style: { background: 'var(--bg-surface)', border: '1px solid var(--primary)', color: 'var(--primary)' }
    });
    try {
      await api.retrainModels();
      await fetchModels();
      toast.success('Models trained successfully!', { id: toastId, style: { background: 'var(--bg-surface)', border: '1px solid var(--profit)', color: 'var(--profit)' } });
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#00D4FF', '#00FF88', '#FFD700']
      });
    } catch (e) {
      console.error('Retrain failed:', e);
      toast.error('Failed to train models', { id: toastId, style: { background: 'var(--bg-surface)', border: '1px solid var(--loss)', color: 'var(--loss)' } });
    }
    setRetraining(false);
  };

  const hasModels = modelResults && Object.keys(modelResults).length > 0;

  return (
    <div>
      {/* Actions */}
      <div className="section-header">
        <div>
          <div className="section-title">ML Model Laboratory</div>
          <div className="section-subtitle">Train, evaluate, and compare ML models for crossover prediction</div>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRetrain}
          disabled={retraining}
          style={{ opacity: retraining ? 0.6 : 1 }}
        >
          {retraining ? '⏳ Training...' : '⟳ Retrain Models'}
        </button>
      </div>

      {!hasModels ? (
        <div className="empty-state" style={{ animation: 'fadeInUp 0.8s ease-out' }}>
          <motion.div 
            className="empty-state-icon"
            animate={{ 
              scale: [1, 1.05, 1],
              opacity: [0.3, 0.5, 0.3] 
            }}
            transition={{ 
              duration: 2.5, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
            style={{ filter: 'drop-shadow(0 0 10px rgba(0,212,255,0.2))' }}
          >🧠</motion.div>
          <div className="empty-state-title">No Models Trained Yet</div>
          <div className="empty-state-desc">
            ML models require at least 50 closed trades for training.
            The system uses chronological train/validation/test splits to prevent data leakage.
          </div>
          
          <div style={{ marginTop: 24, padding: '16px 24px', background: 'var(--bg-surface)', borderRadius: 12, border: '1px solid var(--border-default)', display: 'inline-flex', alignItems: 'center', gap: 12 }}>
             <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid var(--primary)', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }}></div>
             <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Gathering trade data...</span>
          </div>
        </div>
      ) : (
        <>
          {/* Dataset Info */}
          {datasetInfo && Object.keys(datasetInfo).length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ marginBottom: 24 }}
            >
              <div className="section-header" style={{ marginBottom: 16 }}>
                <div className="section-title" style={{ fontSize: 15 }}>Dataset Composition</div>
              </div>
              <div className="grid-metrics">
                {[
                  { label: 'Total Samples', value: datasetInfo.total || 0 },
                  { label: 'Train Set', value: datasetInfo.train_size || 0 },
                  { label: 'Validation Set', value: datasetInfo.val_size || 0 },
                  { label: 'Test Set', value: datasetInfo.test_size || 0 },
                ].map((m, i) => (
                  <motion.div key={m.label} className="glass-card metric-card"
                    initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}>
                    <div className="metric-label">{m.label}</div>
                    <div className="metric-value small">{m.value}</div>
                  </motion.div>
                ))}
              </div>

              {datasetInfo.positive_ratio != null && (
                <div className="glass-card" style={{ marginTop: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Class Distribution</span>
                    <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {formatPercent(datasetInfo.positive_ratio)} profitable
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${(datasetInfo.positive_ratio || 0) * 100}%` }} />
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Model Comparison */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            style={{ marginBottom: 24 }}
          >
            <div className="section-header" style={{ marginBottom: 16 }}>
              <div className="section-title" style={{ fontSize: 15 }}>Model Comparison</div>
            </div>
            <div className="glass-card" style={{ overflow: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Algorithm</th>
                    <th data-tooltip-id="app-tooltip" data-tooltip-content="Area Under the Receiver Operating Characteristic Curve (higher is better)">ROC-AUC ⓘ</th>
                    <th data-tooltip-id="app-tooltip" data-tooltip-content="Percentage of correct predictions overall">Accuracy ⓘ</th>
                    <th data-tooltip-id="app-tooltip" data-tooltip-content="Percentage of correct ACCEPT predictions out of all ACCEPTs">Precision ⓘ</th>
                    <th data-tooltip-id="app-tooltip" data-tooltip-content="Percentage of actual profitable trades correctly identified">Recall ⓘ</th>
                    <th data-tooltip-id="app-tooltip" data-tooltip-content="Harmonic mean of Precision and Recall">F1 ⓘ</th>
                    <th data-tooltip-id="app-tooltip" data-tooltip-content="Optimal probability threshold chosen by the model on validation data">Threshold ⓘ</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(modelResults).map(([name, result]: [string, any]) => {
                    if (result.error) return null;
                    const test = result.test || {};
                    const isBest = name === bestModel;
                    return (
                      <tr key={name} style={{ background: isBest ? 'rgba(255, 215, 0, 0.04)' : undefined }}>
                        <td style={{ fontWeight: 600, color: isBest ? 'var(--accept)' : 'var(--text-primary)' }}>
                          {isBest && '⭐ '}{name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </td>
                        <td className="mono" style={{ color: 'var(--primary)' }}>{test.roc_auc?.toFixed(4) || '—'}</td>
                        <td className="mono">{formatPercent(test.accuracy)}</td>
                        <td className="mono">{formatPercent(test.precision)}</td>
                        <td className="mono">{formatPercent(test.recall)}</td>
                        <td className="mono">{formatPercent(test.f1)}</td>
                        <td className="mono">{result.best_threshold?.toFixed(2) || '—'}</td>
                        <td>
                          {isBest
                            ? <span className="badge badge-accept">ACTIVE</span>
                            : <span className="badge badge-pending">Standby</span>
                          }
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Feature Importance */}
          {featureImportance.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              style={{ marginBottom: 24 }}
            >
              <div className="section-header" style={{ marginBottom: 16 }}>
                <div>
                  <div className="section-title" style={{ fontSize: 15 }}>Feature Importance</div>
                  <div className="section-subtitle">What drives profitability predictions</div>
                </div>
              </div>
              <div className="glass-card">
                <FeatureImportanceChart features={featureImportance} />
              </div>
            </motion.div>
          )}

          {/* Threshold Analysis */}
          {thresholdAnalysis.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <div className="section-header" style={{ marginBottom: 16 }}>
                <div>
                  <div className="section-title" style={{ fontSize: 15 }}>Threshold Analysis</div>
                  <div className="section-subtitle">Evaluated on validation data only (never on test data)</div>
                </div>
              </div>
              <div className="glass-card" style={{ overflow: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Threshold</th>
                      <th>Accepted Win Rate</th>
                      <th>F1 Score</th>
                      <th>Accepted Count</th>
                      <th>Rejected Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {thresholdAnalysis.map((row: any, i: number) => (
                      <tr key={i}>
                        <td className="mono">{row.threshold?.toFixed(2)}</td>
                        <td className="mono">{formatPercent(row.accepted_win_rate)}</td>
                        <td className="mono">{row.f1?.toFixed(4)}</td>
                        <td className="mono">{row.accepted_count || 0}</td>
                        <td className="mono">{row.rejected_count || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* Confusion Matrices */}
          {Object.entries(modelResults).map(([name, result]: [string, any]) => {
            const cm = result?.test?.confusion_matrix;
            if (!cm || cm.length !== 2) return null;
            return (
              <motion.div
                key={name}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                style={{ marginTop: 24 }}
              >
                <div className="section-header" style={{ marginBottom: 16 }}>
                  <div className="section-title" style={{ fontSize: 15 }}>
                    Confusion Matrix — {name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </div>
                </div>
                <div className="glass-card">
                  <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr 1fr', gap: 2, maxWidth: 400 }}>
                    <div />
                    <div style={{ textAlign: 'center', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '8px 0' }}>
                      Pred. Losing
                    </div>
                    <div style={{ textAlign: 'center', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '8px 0' }}>
                      Pred. Profitable
                    </div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '16px 12px', writingMode: 'vertical-lr', transform: 'rotate(180deg)' }}>
                      Actual Losing
                    </div>
                    <div style={{ background: 'rgba(0, 212, 255, 0.08)', padding: 20, textAlign: 'center', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {cm[0][0]}
                    </div>
                    <div style={{ background: 'rgba(255, 51, 102, 0.08)', padding: 20, textAlign: 'center', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--loss)' }}>
                      {cm[0][1]}
                    </div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '16px 12px', writingMode: 'vertical-lr', transform: 'rotate(180deg)' }}>
                      Actual Profitable
                    </div>
                    <div style={{ background: 'rgba(255, 51, 102, 0.08)', padding: 20, textAlign: 'center', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--loss)' }}>
                      {cm[1][0]}
                    </div>
                    <div style={{ background: 'rgba(0, 255, 136, 0.08)', padding: 20, textAlign: 'center', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: 'var(--profit)' }}>
                      {cm[1][1]}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </>
      )}
    </div>
  );
}
