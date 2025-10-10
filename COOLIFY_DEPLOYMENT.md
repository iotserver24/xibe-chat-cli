# 🚀 XIBE-CHAT Analytics Server - Coolify Deployment Guide

## 📋 Overview
This guide will help you deploy the XIBE-CHAT Analytics Server to your Coolify instance to track user usage statistics.

## 🛠️ What You'll Get
- **Real-time analytics dashboard** showing user statistics
- **Anonymous usage tracking** for XIBE-CHAT CLI users
- **Version distribution** and platform statistics
- **RESTful API** for analytics data collection

## 📦 Deployment Steps

### 1. Prepare Your Repository
Make sure these files are in your repository:
- `analytics_server.py` - Main Flask server
- `analytics.py` - Client tracking library
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Service configuration

### 2. Create New Application in Coolify
1. Go to your Coolify dashboard
2. Click **"New Application"**
3. Choose **"Git Repository"**
4. Connect your repository
5. Set the following configuration:

### 3. Application Configuration
```
Application Name: xibe-analytics
Repository: [your-repo-url]
Branch: main/master
Dockerfile: Dockerfile
Port: 5000
```

### 4. Environment Variables
**No environment variables needed!** The analytics server works out of the box.

### 5. Domain Configuration
- **Subdomain**: `xibe-analytics` (or your preferred name)
- **Domain**: Your domain (e.g., `yourdomain.com`)
- **Full URL**: `https://xibe-analytics.yourdomain.com`

### 6. Deploy
1. Click **"Deploy"**
2. Wait for the build to complete
3. Check logs for successful startup

## 🔧 Post-Deployment Configuration

### 1. Update Analytics Server URL
Edit `analytics.py` in your main XIBE-CHAT repository:
```python
ANALYTICS_SERVER_URL = "https://xibe-analytics.yourdomain.com"
```

### 2. Test the Deployment
Visit your analytics dashboard:
```
https://xibe-analytics.yourdomain.com
```

You should see the analytics dashboard with:
- Total unique users: 0 (initially)
- Version distribution
- Platform statistics
- Real-time activity

## 📊 Analytics Dashboard Features

### Real-time Statistics
- **Total Unique Users**: Unique machine IDs that have used XIBE-CHAT
- **Active Users (24h)**: Users active in the last 24 hours
- **Active Users (7d)**: Users active in the last 7 days
- **Events (24h)**: Total events tracked in the last 24 hours

### Data Visualizations
- **Version Distribution**: Which versions users are running
- **Platform Distribution**: Windows/macOS/Linux usage
- **Recent Activity**: Most common events in the last 24 hours

### Auto-refresh
- Dashboard refreshes every 30 seconds automatically
- Manual refresh button available

## 🔒 Privacy & Security

### Anonymous Tracking
- **No personal data** collected
- **Machine IDs** are randomly generated UUIDs
- **No IP addresses** stored
- **No user content** tracked

### Data Collected
- Session start/end times
- Command usage statistics
- Feature usage patterns
- Version and platform information
- Error occurrences (anonymized)

## 🛡️ Security Considerations

### Rate Limiting
The server includes basic rate limiting to prevent abuse.

### Data Retention
- **Sessions**: Stored indefinitely for user counting
- **Events**: Consider implementing cleanup for old events
- **Database**: SQLite file grows over time, monitor disk usage

### Access Control
- Dashboard is publicly accessible (consider adding auth if needed)
- API endpoints are open (consider rate limiting)

## 📈 Monitoring & Maintenance

### Health Checks
- Built-in health check endpoint: `/api/stats`
- Coolify will automatically restart if unhealthy

### Database Backup
The SQLite database is stored in the container. Consider:
- Setting up regular backups
- Using a persistent volume
- Migrating to PostgreSQL for production

### Scaling
For high traffic, consider:
- Using PostgreSQL instead of SQLite
- Adding Redis for session management
- Implementing proper rate limiting
- Adding authentication to the dashboard

## 🔄 Updates

### Updating the Analytics Server
1. Push changes to your repository
2. Coolify will automatically rebuild and deploy
3. Check logs to ensure successful deployment

### Updating Client Tracking
1. Update `analytics.py` in XIBE-CHAT repository
2. Update the server URL if changed
3. Test with a few users before wide deployment

## 📞 Support

### Troubleshooting
1. **Check Coolify logs** for deployment issues
2. **Verify domain configuration** is correct
3. **Test API endpoints** manually:
   ```bash
   curl https://xibe-analytics.yourdomain.com/api/stats
   ```

### Common Issues
- **Port conflicts**: Ensure port 5000 is available
- **Domain issues**: Check DNS configuration
- **Database errors**: Verify file permissions for SQLite

## 🎯 Next Steps

1. **Deploy to Coolify** using this guide
2. **Update XIBE-CHAT** with the new analytics URL
3. **Test with a few users** to verify tracking works
4. **Monitor the dashboard** for incoming data
5. **Set up alerts** for unusual activity or errors

## 📊 Expected Results

After deployment, you should see:
- Analytics dashboard accessible at your domain
- Real-time user statistics
- Command usage patterns
- Version adoption rates
- Platform distribution

The system will start collecting data as soon as users run XIBE-CHAT with the updated analytics configuration.

---

**🚀 Ready to track your XIBE-CHAT users? Deploy now and start collecting valuable insights!**
