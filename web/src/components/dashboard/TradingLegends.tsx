import { motion } from 'framer-motion';

const legends = [
  {
    name: "Rakesh Jhunjhunwala",
    title: "The Big Bull of India",
    quote: "Respect the market. Have an open mind. Know what to stake. Know when to take a loss. Be responsible.",
    image: "https://etimg.etb2bimg.com/photo/93556093.cms",
    gradient: "linear-gradient(135deg, #1E1E2A 0%, #2D1B2E 100%)",
    accent: "#FF6B6B"
  },
  {
    name: "Warren Buffett",
    title: "The Oracle of Omaha",
    quote: "The stock market is a device for transferring money from the impatient to the patient.",
    image: "https://thumbor.forbes.com/thumbor/fit-in/416x416/filters%3Aformat%28jpg%29/https%3A%2F%2Fspecials-images.forbesimg.com%2Fimageserve%2F59d502f931358e542c034e76%2F0x0.jpg",
    gradient: "linear-gradient(135deg, #1A202C 0%, #173242 100%)",
    accent: "#4ECCA3"
  },
  {
    name: "Jim Simons",
    title: "The Quant King",
    quote: "We search through historical data looking for anomalous patterns that we would not expect to occur at random.",
    image: "https://www.simonsfoundation.org/wp-content/uploads/2017/08/Jim-Simons-Portrait-2017-Web.jpg",
    gradient: "linear-gradient(135deg, #1F1C2C 0%, #232526 100%)",
    accent: "#9D4EDD"
  }
];

export default function TradingLegends() {
  return (
    <div style={{ marginTop: '64px', marginBottom: '48px' }}>
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.5px' }}>
          Legends of Trading
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px', marginTop: '8px', fontWeight: 500 }}>
          Timeless wisdom from the masters of the market.
        </p>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '32px', alignItems: 'stretch' }}>
        {legends.map((legend, index) => (
          <motion.div
            key={legend.name}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.15, ease: [0.16, 1, 0.3, 1] }}
            whileHover={{ y: -8, scale: 1.02 }}
            style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              padding: '32px', 
              position: 'relative', 
              overflow: 'hidden', 
              height: '100%',
              background: legend.gradient,
              borderRadius: '24px',
              boxShadow: '0 20px 40px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.05)',
              color: 'white'
            }}
          >
            {/* Massive decorative quote mark in background */}
            <span style={{ 
              position: 'absolute', 
              top: '-20px', 
              right: '20px', 
              fontSize: '180px', 
              color: legend.accent, 
              opacity: 0.1, 
              fontFamily: 'Georgia, serif',
              lineHeight: 1,
              userSelect: 'none'
            }}>
              "
            </span>
            
            {/* Glowing orb accent */}
            <div style={{ position: 'absolute', bottom: '-50px', left: '-50px', width: '150px', height: '150px', background: legend.accent, filter: 'blur(80px)', opacity: 0.15, borderRadius: '50%' }} />

            <div style={{ flex: 1, position: 'relative', display: 'flex', alignItems: 'flex-start', marginBottom: '32px', zIndex: 1 }}>
              <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.9)', lineHeight: 1.7, fontStyle: 'italic', fontWeight: 500 }}>
                "{legend.quote}"
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', zIndex: 1, marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', overflow: 'hidden', border: `2px solid ${legend.accent}`, flexShrink: 0, background: '#fff', boxShadow: `0 0 15px ${legend.accent}40` }}>
                <img 
                  src={legend.image} 
                  alt={legend.name} 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  onError={(e) => { 
                    const fallbackName = legend.name.replace(' ', '+');
                    e.currentTarget.src = `https://ui-avatars.com/api/?name=${fallbackName}&background=random&color=fff&size=128&bold=true`; 
                  }} 
                />
              </div>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#fff', letterSpacing: '0.3px' }}>{legend.name}</div>
                <div style={{ fontSize: '13px', color: legend.accent, fontWeight: 600, marginTop: '2px', textTransform: 'uppercase', letterSpacing: '1px' }}>{legend.title}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
