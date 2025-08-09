# Security Policy

## Overview

**Webamon Search CLI** is a threat intelligence tool that interfaces with the Webamon API to provide cybersecurity professionals with access to threat data. We take security seriously and appreciate the security community's efforts to responsibly disclose vulnerabilities.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability in Webamon CLI, please report it responsibly:

**🔒 Private Disclosure (Preferred)**
- Email: `security@webamon.com`
- Subject: `[SECURITY] Webamon CLI Vulnerability Report`
- Include: Detailed description, reproduction steps, and impact assessment

**📋 GitHub Security Advisory**
- Use GitHub's [Private Vulnerability Reporting](https://github.com/webamon-org/webamon-cli/security/advisories/new)
- This allows us to collaborate privately before disclosure

### What to Include

Please provide as much information as possible:

- **Vulnerability Type**: Authentication, injection, data exposure, etc.
- **Component Affected**: CLI code, API interaction, configuration, etc.
- **Reproduction Steps**: Clear instructions to reproduce the issue
- **Impact Assessment**: What could an attacker achieve?
- **Suggested Fix**: If you have ideas for remediation
- **Your Details**: Name and contact info for credit (optional)

### Response Timeline

We are committed to addressing security issues promptly:

- **24 hours**: Initial acknowledgment of your report
- **72 hours**: Preliminary assessment and severity classification
- **7 days**: Detailed investigation and response plan
- **30 days**: Target for fix implementation and release
- **90 days**: Public disclosure after fix is available

## Security Considerations

### API Key Security

**🔑 Protecting Your API Key:**

- **Never commit API keys** to version control
- **Use environment variables** or secure configuration files
- **Restrict API key permissions** to minimum required scope
- **Rotate API keys regularly** (quarterly recommended)
- **Monitor API usage** for unusual activity

**❌ Insecure Practices:**
```bash
# DON'T: Hard-code API keys
webamon search --api-key YOUR_SECRET_KEY_HERE example.com

# DON'T: Expose in shell history
export WEBAMON_API_KEY=your-secret-key && webamon search example.com
```

**✅ Secure Practices:**
```bash
# DO: Use configuration file
webamon configure  # Stores securely in ~/.webamon/config.json

# DO: Use environment variables
export WEBAMON_API_KEY="$(cat ~/.secrets/webamon-key)"
webamon search example.com
```

### Data Handling

**🛡️ Sensitive Data Protection:**

- **Exported files** may contain sensitive threat intelligence data
- **Configure appropriate file permissions** for exports
- **Use secure storage** for exported threat data
- **Follow data retention policies** for your organization
- **Sanitize data** before sharing or posting examples

**📁 Secure File Handling:**
```bash
# Set restrictive permissions on exported files
webamon search malware.com --export sensitive-data.json
chmod 600 sensitive-data.json

# Use secure temporary directories
export TMPDIR=/secure/temp
webamon search --format csv threat-data
```

### Network Security

**🌐 Secure Communications:**

- All API communications use **HTTPS/TLS encryption**
- Certificate validation is **always enforced**
- No sensitive data is logged in network requests
- API endpoints use **modern TLS protocols** (TLS 1.2+)

### Configuration Security

**⚙️ Secure Configuration:**

- Configuration files are stored with restricted permissions (600)
- No passwords or secrets in command history
- Configuration validation prevents injection attacks
- Secure defaults for all settings

## Common Security Issues

### Input Validation

The CLI validates all user inputs to prevent:
- **Command injection** via malicious search terms
- **Path traversal** in export file names
- **JSON injection** in API parameters
- **Header injection** in HTTP requests

### Error Handling

We follow secure error handling practices:
- **No sensitive data** in error messages
- **Generic error responses** for failed authentication
- **Rate limiting information** is not exposed
- **Stack traces** are sanitized in production

## Security Best Practices for Users

### Environment Setup

1. **Keep CLI Updated**: Always use the latest version
   ```bash
   pipx upgrade webamon-cli
   ```

2. **Secure Installation**: Use official sources only
   ```bash
   # Official PyPI
   pipx install webamon-cli
   
   # Official GitHub
   git clone https://github.com/webamon-org/webamon-cli.git
   ```

3. **Verify Installation**: Check for unexpected modifications
   ```bash
   webamon --version
   webamon status
   ```

### Operational Security

1. **Limit API Access**: Use read-only API keys when possible
2. **Monitor Usage**: Regularly review API usage logs
3. **Secure Exports**: Encrypt sensitive exported data
4. **Network Isolation**: Use VPNs or secure networks for sensitive queries
5. **Log Management**: Securely store and rotate CLI logs

### Incident Response

If you suspect your API key or system is compromised:

1. **Immediately revoke** the API key at https://webamon.com/account
2. **Generate a new API key** with appropriate permissions
3. **Review recent API usage** for unauthorized activity
4. **Update CLI configuration** with new credentials
5. **Report the incident** to security@webamon.com

## Vulnerability Disclosure Policy

### Coordinated Disclosure

We believe in coordinated disclosure that:
- Protects users while issues are being fixed
- Gives security researchers appropriate credit
- Maintains transparency with the community
- Follows industry best practices

### Public Disclosure

After fixes are released:
- **Security advisories** will be published on GitHub
- **CVE numbers** will be assigned for significant vulnerabilities
- **Release notes** will include security fix details
- **Blog posts** may provide additional context

### Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- **Credited** in security advisories and release notes
- **Listed** in our security acknowledgments
- **Invited** to beta test security fixes (if desired)
- **Eligible** for our security researcher recognition program

## Contact Information

**Security Team**: security@webamon.com  
**General Contact**: info@webamon.com  
**GitHub Issues**: https://github.com/webamon-org/webamon-cli/issues  
**Security Advisories**: https://github.com/webamon-org/webamon-cli/security/advisories

## Additional Resources

- [Webamon Security Center](https://webamon.com/security)
- [API Security Documentation](https://docs.webamon.com/security)
- [Responsible Disclosure Guidelines](https://webamon.com/responsible-disclosure)

---

**Thank you for helping keep Webamon CLI and our users secure!** 🛡️

*Last updated: January 2025*