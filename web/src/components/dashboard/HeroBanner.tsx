import { motion } from 'framer-motion';

export default function HeroBanner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'relative',
        padding: '48px 40px',
        marginBottom: '40px',
        borderRadius: '24px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        background: 'linear-gradient(135deg, rgba(20,20,25,0.8) 0%, rgba(30,35,45,0.9) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1)'
      }}
    >
      {/* Background glow effects */}
      <div style={{ position: 'absolute', top: '-100px', left: '-100px', width: '300px', height: '300px', background: 'var(--primary)', filter: 'blur(100px)', opacity: 0.15, borderRadius: '50%' }} />
      <div style={{ position: 'absolute', bottom: '-100px', right: '-100px', width: '300px', height: '300px', background: 'var(--profit)', filter: 'blur(100px)', opacity: 0.1, borderRadius: '50%' }} />
      
      {/* Abstract geometric background elements resembling steps */}
      <div style={{ position: 'absolute', right: '10%', bottom: '20%', width: '200px', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)', transform: 'rotate(-45deg)' }} />
      <div style={{ position: 'absolute', right: '15%', bottom: '35%', width: '150px', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)', transform: 'rotate(-45deg)' }} />
      <div style={{ position: 'absolute', right: '20%', bottom: '50%', width: '100px', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)', transform: 'rotate(-45deg)' }} />

      <h2 style={{ fontSize: '32px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '16px', letterSpacing: '-0.5px' }}>
        The top isn't luck. <span style={{ color: 'var(--primary)' }}>It's earned.</span>
      </h2>
      
      <p style={{ fontSize: '16px', color: 'var(--text-secondary)', lineHeight: 1.8, maxWidth: '800px', fontWeight: 500 }}>
        Success isn’t built in one leap. It starts with a goal. Turns into a plan. Backed by relentless action. Strengthened by discipline. Fueled by obsession. <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Step by step — you climb.</span>
      </p>
    </motion.div>
  );
}
