"""
NestJS Notification Emitter Module.

Module này generate NestJS code cho CP12 Notification Emitter:
- NotificationModule: NestJS module với providers
- NotificationService: Service class mirroring FastAPI service
- NotificationController: REST endpoints
- Gateway interfaces: EmailGateway, SmsGateway, PushGateway

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.emitters.core.notification.models import (
    NotificationChannel,
    NotificationTemplate,
)


# ============================================================================
# NestJS Notification Emitter
# ============================================================================


class NestJSNotificationEmitter:
    """
    Emitter cho NestJS notification code.

    Generate các file TypeScript cho notification system bao gồm:
    - Module (NotificationModule)
    - Service (NotificationService)
    - Controller (NotificationController)
    - Gateway interfaces
    """

    def generate_module(self) -> str:
        """
        Generate NotificationModule.

        Returns:
            String chứa TypeScript code cho NotificationModule
        """
        return '''"""
Notification Module.

Module NestJS cho notification system bao gồm:
- NotificationService
- NotificationController
- Gateway providers

Author: Midicoder Team
Version: 1.0.0
"""

import { Module, Global } from "@nestjs/common";
import { EventsModule } from "@nestjs/event-emitter";

import { NotificationService } from "./notification.service";
import { NotificationController } from "./notification.controller";

@Global()
@Module({
  imports: [EventsModule],
  providers: [NotificationService],
  controllers: [NotificationController],
  exports: [NotificationService],
})
export class NotificationModule {}
'''

    def generate_service(self) -> str:
        """
        Generate NotificationService class.

        Returns:
            String chứa TypeScript code cho NotificationService
        """
        return '''"""
Notification Service.

Service chính cho notification system trong NestJS.
Quản lý templates, providers, va dispatch notifications.

Author: Midicoder Team
Version: 1.0.0
"""

import { Injectable, Logger } from "@nestjs/common";
import { EventEmitter2 } from "@nestjs/event-emitter";
import { v4 as uuidv4 } from "uuid";

// ============================================================================
// Enums & Interfaces
// ============================================================================

export enum NotificationChannel {
  EMAIL = "email",
  SMS = "sms",
  PUSH = "push",
  WEBHOOK = "webhook",
  IN_APP = "in_app",
}

export interface DispatchResult {
  dispatch_id: string;
  status: "pending" | "sent" | "failed" | "bounced";
  provider_response?: Record<string, any>;
  error_code?: string;
}

export interface NotificationTemplate {
  template_id: string;
  channel: NotificationChannel;
  subject: string;
  body_html: string;
  body_text: string;
  variables: string[];
  locale: string;
}

export interface NotificationGateway {
  send(
    recipient: string,
    subject: string,
    body: string,
    metadata?: Record<string, any>,
  ): Promise<DispatchResult>;
}

// ============================================================================
// NotificationService
// ============================================================================

@Injectable()
export class NotificationService {
  private readonly logger = new Logger(NotificationService.name);
  private templates: Map<string, NotificationTemplate> = new Map();
  private gateways: Map<NotificationChannel, NotificationGateway[]> = new Map();
  private rateLimits: Record<string, number> = {
    email: 100,
    sms: 10,
    push: 1000,
    webhook: 100,
    in_app: 1000,
  };

  constructor(private eventEmitter: EventEmitter2) {}

  /**
   * Dang ky notification template.
   */
  registerTemplate(template: NotificationTemplate): void {
    this.templates.set(template.template_id, template);
    this.logger.log(\`Template registered: \${template.template_id}\`);
  }

  /**
   * Render template voi variable values.
   * Thay the {{variable}} trong template bang values tu data.
   */
  renderTemplate(
    templateId: string,
    data: Record<string, any>,
  ): { subject: string; body_html: string; body_text: string } {
    const template = this.templates.get(templateId);
    if (!template) {
      throw new Error(\`MDC-CP12-002: Template not found: \${templateId}\`);
    }

    const render = (text: string): string =>
      text.replace(/\\{\\{(\\w+)\\}\\}/g, (match, varName) =>
        data[varName] !== undefined ? String(data[varName]) : match,
      );

    return {
      subject: render(template.subject),
      body_html: render(template.body_html),
      body_text: render(template.body_text),
    };
  }

  /**
   * Gui email notification.
   */
  async sendEmail(
    recipient: string,
    subject: string,
    bodyHtml: string,
  ): Promise<DispatchResult> {
    const dispatchId = \`email_\${uuidv4()}\`;
    const gateways = this.gateways.get(NotificationChannel.EMAIL) || [];

    if (gateways.length === 0) {
      return {
        dispatch_id: dispatchId,
        status: "failed",
        error_code: "MDC-CP12-004",
      };
    }

    try {
      const result = await gateways[0].send(recipient, subject, bodyHtml);
      result.dispatch_id = dispatchId;
      this.logger.log(\`Email sent: \${dispatchId} to \${recipient}\`);
      this.eventEmitter.emit("notification.sent", result);
      return result;
    } catch (error) {
      this.logger.error(\`Email dispatch failed: \${error.message}\`);
      return {
        dispatch_id: dispatchId,
        status: "failed",
        error_code: "MDC-CP12-005",
      };
    }
  }

  /**
   * Gui SMS notification.
   */
  async sendSms(recipient: string, bodyText: string): Promise<DispatchResult> {
    const dispatchId = \`sms_\${uuidv4()}\`;
    const gateways = this.gateways.get(NotificationChannel.SMS) || [];

    if (gateways.length === 0) {
      return {
        dispatch_id: dispatchId,
        status: "failed",
        error_code: "MDC-CP12-004",
      };
    }

    try {
      const result = await gateways[0].send(recipient, "", bodyText);
      result.dispatch_id = dispatchId;
      this.logger.log(\`SMS sent: \${dispatchId} to \${recipient}\`);
      this.eventEmitter.emit("notification.sent", result);
      return result;
    } catch (error) {
      this.logger.error(\`SMS dispatch failed: \${error.message}\`);
      return {
        dispatch_id: dispatchId,
        status: "failed",
        error_code: "MDC-CP12-005",
      };
    }
  }

  /**
   * Gui push notification.
   */
  async sendPush(
    recipient: string,
    title: string,
    body: string,
  ): Promise<DispatchResult> {
    const dispatchId = \`push_\${uuidv4()}\`;
    const gateways = this.gateways.get(NotificationChannel.PUSH) || [];

    if (gateways.length === 0) {
      return {
        dispatch_id: dispatchId,
        status: "failed",
        error_code: "MDC-CP12-004",
      };
    }

    try {
      const result = await gateways[0].send(recipient, title, body);
      result.dispatch_id = dispatchId;
      this.logger.log(\`Push sent: \${dispatchId} to \${recipient}\`);
      this.eventEmitter.emit("notification.sent", result);
      return result;
    } catch (error) {
      this.logger.error(\`Push dispatch failed: \${error.message}\`);
      return {
        dispatch_id: dispatchId,
        status: "failed",
        error_code: "MDC-CP12-005",
      };
    }
  }

  /**
   * Dispatch notification dua tren template.
   */
  async dispatch(
    templateId: string,
    recipient: string,
    payload: Record<string, any>,
    channel?: NotificationChannel,
  ): Promise<DispatchResult> {
    const rendered = this.renderTemplate(templateId, payload);
    const template = this.templates.get(templateId);
    const targetChannel = channel || template.channel;

    switch (targetChannel) {
      case NotificationChannel.EMAIL:
        return this.sendEmail(recipient, rendered.subject, rendered.body_html);
      case NotificationChannel.SMS:
        return this.sendSms(recipient, rendered.body_text);
      case NotificationChannel.PUSH:
        return this.sendPush(recipient, rendered.subject, rendered.body_text);
      default:
        throw new Error(\`MDC-CP12-001: Channel not supported: \${targetChannel}\`);
    }
  }
}
'''

    def generate_controller(self) -> str:
        """
        Generate NotificationController.

        Returns:
            String chứa TypeScript code cho NotificationController
        """
        return '''"""
Notification Controller.

Controller cho notification REST endpoints:
- POST /api/notifications/dispatch - Dispatch single notification
- POST /api/notifications/batch - Batch dispatch notifications  
- GET /api/notifications/:dispatchId - Get dispatch status

Author: Midicoder Team
Version: 1.0.0
"""

import {
  Controller,
  Post,
  Get,
  Body,
  Param,
  HttpCode,
  HttpStatus,
} from "@nestjs/common";

import { NotificationService, DispatchResult } from "./notification.service";

@Controller("api/notifications")
export class NotificationController {
  constructor(private readonly notificationService: NotificationService) {}

  /**
   * Dispatch single notification.
   */
  @Post("dispatch")
  @HttpCode(HttpStatus.ACCEPTED)
  async dispatchNotification(
    @Body() body: { template_id: string; recipient: string; payload: Record<string, any>; channel?: string },
  ): Promise<DispatchResult> {
    return this.notificationService.dispatch(
      body.template_id,
      body.recipient,
      body.payload,
      body.channel ? (body.channel as any) : undefined,
    );
  }

  /**
   * Batch dispatch notifications.
   */
  @Post("batch")
  @HttpCode(HttpStatus.ACCEPTED)
  async batchDispatch(
    @Body() body: { dispatches: Array<{ template_id: string; recipient: string; payload: Record<string, any>; channel?: string }> },
  ): Promise<DispatchResult[]> {
    const results: DispatchResult[] = [];
    for (const item of body.dispatches) {
      const result = await this.notificationService.dispatch(
        item.template_id,
        item.recipient,
        item.payload,
        item.channel ? (item.channel as any) : undefined,
      );
      results.push(result);
    }
    return results;
  }

  /**
   * Get dispatch status.
   */
  @Get(":dispatchId")
  async getDispatchStatus(
    @Param("dispatchId") dispatchId: string,
  ): Promise<DispatchResult> {
    // TODO: Query dispatch log tu database
    return {
      dispatch_id: dispatchId,
      status: "pending",
    };
  }
}
'''

    def generate_interfaces(self) -> str:
        """
        Generate gateway interfaces.

        Returns:
            String chứa TypeScript code cho gateway interfaces
        """
        return '''"""
Notification Gateway Interfaces.

Cac interface cho notification provider gateways.
Cac concrete provider (SendGrid, Twilio, Firebase) implement cac interface nay.

Author: Midicoder Team
Version: 1.0.0
"""

import { DispatchResult } from "./notification.service";

/**
 * Email Gateway Interface.
 * Implement de gui email (SendGrid, SES, v.v.).
 */
export interface EmailGateway {
  send(
    to: string,
    subject: string,
    bodyHtml: string,
    options?: {
      from?: string;
      replyTo?: string;
      attachments?: Array<{ filename: string; content: Buffer; contentType: string }>;
    },
  ): Promise<DispatchResult>;
}

/**
 * SMS Gateway Interface.
 * Implement de gui SMS (Twilio, v.v.).
 */
export interface SmsGateway {
  send(
    to: string,
    message: string,
    options?: {
      from?: string;
    },
  ): Promise<DispatchResult>;
}

/**
 * Push Gateway Interface.
 * Implement de gui push notification (Firebase, APNs).
 */
export interface PushGateway {
  send(
    deviceToken: string,
    title: string,
    body: string,
    options?: {
      badge?: number;
      sound?: string;
      data?: Record<string, any>;
    },
  ): Promise<DispatchResult>;
}

/**
 * Webhook Gateway Interface.
 * Implement de gui webhook HTTP POST.
 */
export interface WebhookGateway {
  send(
    url: string,
    payload: Record<string, any>,
    options?: {
      headers?: Record<string, string>;
      timeout?: number;
    },
  ): Promise<DispatchResult>;
}
'''

    def generate(self) -> dict[str, str]:
        """
        Generate toan bo notification files.

        Returns:
            Dictionary mapping file path -> code content
        """
        return {
            "notification/notification.module.ts": self.generate_module(),
            "notification/notification.service.ts": self.generate_service(),
            "notification/notification.controller.ts": self.generate_controller(),
            "notification/gateways.ts": self.generate_interfaces(),
        }