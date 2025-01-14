const response = await fetch('https://your-ngrok-url/make_call', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phoneNumber })
});
