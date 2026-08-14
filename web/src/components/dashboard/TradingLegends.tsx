import { motion } from 'framer-motion';

const legends = [
  {
    name: "Rakesh Jhunjhunwala",
    title: "The Big Bull of India",
    quote: "Respect the market. Have an open mind. Know what to stake. Know when to take a loss. Be responsible.",
    image: "https://images.livemint.com/img/2022/08/14/1600x900/Rakesh_Jhunjhunwala_1660447035544_1660447035767_1660447035767.PNG"
  },
  {
    name: "Warren Buffett",
    title: "The Oracle of Omaha",
    quote: "The stock market is a device for transferring money from the impatient to the patient.",
    image: "https://image.cnbcfm.com/api/v1/image/107228941-1682027700192-gettyimages-1240375220-NOMAHA_BERKSHIRE_HATHAWAY.jpeg"
  },
  {
    name: "Jim Simons",
    title: "The Quant King",
    quote: "We search through historical data looking for anomalous patterns that we would not expect to occur at random.",
    image: "https://d1e00ek4ebabms.cloudfront.net/production/2c892b15-99d9-482d-a2f0-ce8c230559eb.jpg"
  }
];

export default function TradingLegends() {
  return (
    <div style={{ marginTop: '48px', marginBottom: '32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)' }}>Legends of Trading</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>Timeless wisdom from the masters of the market.</p>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', alignItems: 'stretch' }}>
        {legends.map((legend, index) => (
          <motion.div
            key={legend.name}
            className="glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            style={{ display: 'flex', flexDirection: 'column', padding: '24px', position: 'relative', overflow: 'hidden', height: '100%' }}
          >
            {/* Background Accent */}
            <div style={{ position: 'absolute', top: '-50px', right: '-50px', width: '100px', height: '100px', background: 'var(--primary)', filter: 'blur(50px)', opacity: 0.1, borderRadius: '50%' }} />
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
              <div style={{ width: '60px', height: '60px', borderRadius: '50%', overflow: 'hidden', border: '2px solid var(--border-default)', flexShrink: 0 }}>
                <img 
                  src={legend.image} 
                  alt={legend.name} 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  onError={(e) => { 
                    e.currentTarget.src = 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&q=80&w=200'; 
                  }} 
                />
              </div>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>{legend.name}</div>
                <div style={{ fontSize: '13px', color: 'var(--primary)', fontWeight: 500 }}>{legend.title}</div>
              </div>
            </div>
            
            <div style={{ flex: 1, position: 'relative', display: 'flex', alignItems: 'center' }}>
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
