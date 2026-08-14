import { motion, type Variants } from 'framer-motion';

const containerVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.6, 
      ease: [0.16, 1, 0.3, 1],
      staggerChildren: 0.15
    }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
};

export default function HeroBanner() {
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768;
  
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      style={{
        position: 'relative',
        padding: isMobile ? '24px 16px' : '48px 40px',
        marginBottom: isMobile ? '20px' : '40px',
        borderRadius: isMobile ? '16px' : '24px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        background: 'linear-gradient(135deg, rgba(15,15,20,0.95) 0%, rgba(30,35,45,0.98) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.1)'
      }}
    >
      {/* Background glow effects with continuous pulsing animation */}
      <motion.div 
        animate={{ scale: [1, 1.2, 1], opacity: [0.1, 0.15, 0.1] }} 
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        style={{ position: 'absolute', top: '-100px', left: '-100px', width: '300px', height: '300px', background: '#00E5FF', filter: 'blur(100px)', borderRadius: '50%' }} 
      />
      <motion.div 
        animate={{ scale: [1, 1.3, 1], opacity: [0.05, 0.1, 0.05] }} 
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        style={{ position: 'absolute', bottom: '-100px', right: '-100px', width: '300px', height: '300px', background: '#00D09C', filter: 'blur(100px)', borderRadius: '50%' }} 
      />
      
      {/* Abstract geometric background elements resembling steps with floating animation */}
      <motion.div 
        animate={{ x: [-5, 5, -5], y: [-5, 5, -5] }} transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        style={{ position: 'absolute', right: '10%', bottom: '20%', width: '200px', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)', transform: 'rotate(-45deg)' }} 
      />
      <motion.div 
        animate={{ x: [5, -5, 5], y: [5, -5, 5] }} transition={{ duration: 7, repeat: Infinity, ease: "linear" }}
        style={{ position: 'absolute', right: '15%', bottom: '35%', width: '150px', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)', transform: 'rotate(-45deg)' }} 
      />
      <motion.div 
        animate={{ x: [-8, 8, -8], y: [-8, 8, -8] }} transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
        style={{ position: 'absolute', right: '20%', bottom: '50%', width: '100px', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)', transform: 'rotate(-45deg)' }} 
      />

      <motion.h2 variants={itemVariants} style={{ position: 'relative', zIndex: 1, fontSize: isMobile ? 'clamp(18px, 6vw, 28px)' : '32px', fontWeight: 800, color: '#ffffff', marginBottom: isMobile ? '12px' : '16px', letterSpacing: '-0.5px', lineHeight: 1.2 }}>
        The top isn't luck. <span style={{ color: '#00E5FF' }}>It's earned.</span>
      </motion.h2>
      
      <motion.p variants={itemVariants} style={{ position: 'relative', zIndex: 1, fontSize: isMobile ? 'clamp(12px, 3vw, 15px)' : '16px', color: 'rgba(255,255,255,0.7)', lineHeight: 1.6, maxWidth: '800px', fontWeight: 500, margin: 0 }}>
        Success isn’t built in one leap. It starts with a goal. Turns into a plan. Backed by relentless action. Strengthened by discipline. Fueled by obsession. <span style={{ color: '#ffffff', fontWeight: 600 }}>Step by step — you climb.</span>
      </motion.p>
    </motion.div>
  );
}
