/**
 * Vercel Serverless Function для отправки ежедневной рассылки
 * Запускается через Vercel Cron Jobs
 */

export default async function handler(req, res) {
  // Проверяем секретный ключ (для безопасности при использовании внешних cron)
  const cronSecret = req.headers['x-cron-secret'] || req.query.secret;
  const expectedSecret = process.env.CRON_SECRET;
  
  if (expectedSecret && cronSecret !== expectedSecret) {
    return res.status(401).json({ 
      error: 'Unauthorized',
      message: 'Invalid cron secret' 
    });
  }
  
  // Проверяем метод (для Vercel Cron должен быть GET)
  if (req.method !== 'GET' && req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    // Импортируем и запускаем Python скрипт через child_process
    const { spawn } = require('child_process');
    const path = require('path');
    
    return new Promise((resolve, reject) => {
      const pythonScript = spawn('python3', [
        path.join(process.cwd(), 'send_daily.py')
      ], {
        env: {
          ...process.env,
          BOT_TOKEN: process.env.BOT_TOKEN,
          GRAPHQL_ENDPOINT: process.env.GRAPHQL_ENDPOINT,
          GROUP_CHAT_ID: process.env.GROUP_CHAT_ID,
          CALENDAR_URL: process.env.CALENDAR_URL
        }
      });
      
      let output = '';
      let errorOutput = '';
      
      pythonScript.stdout.on('data', (data) => {
        output += data.toString();
        console.log(data.toString());
      });
      
      pythonScript.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error(data.toString());
      });
      
      pythonScript.on('close', (code) => {
        if (code === 0) {
          res.status(200).json({
            status: 'success',
            message: 'Daily digest sent successfully',
            output: output
          });
          resolve();
        } else {
          res.status(500).json({
            status: 'error',
            message: 'Failed to send daily digest',
            error: errorOutput,
            code: code
          });
          reject(new Error(`Python script exited with code ${code}`));
        }
      });
      
      pythonScript.on('error', (error) => {
        res.status(500).json({
          status: 'error',
          message: 'Failed to start Python script',
          error: error.message
        });
        reject(error);
      });
    });
    
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({
      status: 'error',
      message: 'Internal server error',
      error: error.message
    });
  }
}

