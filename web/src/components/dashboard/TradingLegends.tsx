import { motion } from 'framer-motion';

const legends = [
  {
    name: "Rakesh Jhunjhunwala",
    title: "The Big Bull of India",
    quote: "Respect the market. Have an open mind. Know what to stake. Know when to take a loss. Be responsible.",
    image: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Rakesh_Jhunjhunwala.jpg/800px-Rakesh_Jhunjhunwala.jpg"
  },
  {
    name: "Warren Buffett",
    title: "The Oracle of Omaha",
    quote: "The stock market is a device for transferring money from the impatient to the patient.",
    image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Warren_Buffett_KU_School_of_Business_2017.jpg/800px-Warren_Buffett_KU_School_of_Business_2017.jpg"
  },
  {
    name: "Jim Simons",
    title: "The Quant King",
    quote: "We search through historical data looking for anomalous patterns that we would not expect to occur at random.",
    image: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Jim_Simons_1993.jpg/800px-Jim_Simons_1993.jpg"
  }
];

export default function TradingLegends() {
  return (
    <div style={{ marginTop: '48px', marginBottom: '32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)' }}>Legends of Trading</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>Timeless wisdom from the masters of the market.</p>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        {legends.map((legend, index) => (
          <motion.div
            key={legend.name}
            className="glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            style={{ display: 'flex', flexDirection: 'column', padding: '24px', position: 'relative', overflow: 'hidden' }}
          >
            {/* Background Accent */}
            <div style={{ position: 'absolute', top: '-50px', right: '-50px', width: '100px', height: '100px', background: 'var(--primary)', filter: 'blur(50px)', opacity: 0.1, borderRadius: '50%' }} />
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
              <div style={{ width: '60px', height: '60px', borderRadius: '50%', overflow: 'hidden', border: '2px solid var(--border-default)' }}>
                <img 
                  src={legend.image} 
                  alt={legend.name} 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  onError={(e) => { 
                    // Fallback to a nice generic finance placeholder if Wikipedia image fails
                    e.currentTarget.src = 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&q=80&w=200'; 
                  }} 
                />
              </div>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>{legend.name}</div>
                <div style={{ fontSize: '13px', color: 'var(--primary)', fontWeight: 500 }}>{legend.title}</div>
              </div>
            </div>
            
            <div style={{ flex: 1, position: 'relative' }}>
              <span style={{ position: 'absolute', top: '-10px', left: '-10px', fontSize: '40px', color: 'var(--text-muted)', opacity: 0.2, fontFamily: 'serif' }}>"</span>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.6, fontStyle: 'italic', zIndex: 1, position: 'relative' }}>
                {legend.quote}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
