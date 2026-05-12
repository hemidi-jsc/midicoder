"""
NestJS Notification Emitter.

Module này generate NestJS code cho CP12 Notification Emitter:
- NotificationModule: NestJS module
- NotificationService: Service class
- NotificationController: REST controller
- DTOs: Request/Response schemas
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GeneratedFile:
    """File đã generate từ emitter."""
    path: Path
    content: str
    template: str
    capability: str = "CP12"


class NestJSNotificationEmitter:
    """
    Emitter generate NestJS code cho notification.

    Generate:
    - notification.module.ts: NestJS module
    - notification.service.ts: Service class
    - notification.controller.ts: REST controller
    - notification.dto.ts: DTOs
    """

    def generate(self) -> dict[str, str]:
        """
        Generate toàn bộ NestJS notification code.

        Returns:
            Dict mapping file_path -> code content
        """
        return {
            "src/notification/notification.module.ts": self.generate_module(),
            "src/notification/notification.service.ts": self.generate_service(),
            "src/notification/notification.controller.ts": self.generate_controller(),
            "src/notification/notification.dto.ts": self.generate_dto(),
        }

    def generate_module(self) -> str:
        """Generate NotificationModule."""
        return textwrap.dedent('''\
            /**
             * Notification Module - CP12: Notification & Communication
             *
             * NestJS module cho notification dispatch đa kênh.
             */

            import { Module } from '@nestjs/common';
            import { NotificationService } from './notification.service';
            import { NotificationController } from './notification.controller';

            @Module({
              providers: [NotificationService],
              controllers: [NotificationController],
              exports: [NotificationService],
            })
            export class NotificationModule {}
            ''')

    def generate_service(self) -> str:
        """Generate NotificationService."""
        return textwrap.dedent('''\
            /**
             * Notification Service - CP12: Notification & Communication
             *
             * Service này xử lý notification dispatch cho đa kênh (email, SMS, push).
             * Support template rendering, rate limiting, và multi-channel dispatch.
             */

            import { Injectable, BadRequestException } from '@nestjs/common';

            export enum NotificationChannel {
              EMAIL = 'email',
              SMS = 'sms',
              PUSH = 'push',
              WEBHOOK = 'webhook',
              IN_APP = 'in_app',
            }

            export interface NotificationTemplate {
              templateId: string;
              channel: NotificationChannel;
              subject: string;
              bodyHtml: string;
              bodyText: string;
              variables?: string[];
              locale?: string;
            }

            export interface DispatchResult {
              status: string;
              recipient: string;
              channel: string;
              timestamp: string;
            }

            @Injectable()
            export class NotificationService {
              private templates: Map<string, NotificationTemplate> = new Map();
              private dispatchLog: DispatchResult[] = [];
              private rateLimits: Map<string, { count: number; windowStart: number }> = new Map();

              /** Đăng ký notification template. */
              registerTemplate(template: NotificationTemplate): void {
                this.templates.set(template.templateId, template);
              }

              /** Lấy template theo ID. */
              getTemplate(templateId: string): NotificationTemplate | undefined {
                return this.templates.get(templateId);
              }

              /** Liệt kê tất cả templates. */
              listTemplates(): NotificationTemplate[] {
                return Array.from(this.templates.values());
              }

              /**
               * Gửi email notification.
               *
               * @param recipient - Email address người nhận
               * @param templateId - ID của template
               * @param payload - Variable values cho template rendering
               */
              async sendEmail(
                recipient: string,
                templateId: string,
                payload?: Record<string, any>,
              ): Promise<DispatchResult> {
                const template = this.templates.get(templateId);
                if (!template) {
                  throw new Error(`MDC-CP12-002: Template not found: ${templateId}`);
                }

                this.checkRateLimit(recipient, 'email');
                const rendered = this.renderTemplate(template, payload || {});

                const result = await this.dispatchEmail(recipient, rendered);
                this.logDispatch(templateId, recipient, 'email', result.status);
                return result;
              }

              /**
               * Gửi SMS notification.
               *
               * @param recipient - Số điện thoại người nhận
               * @param templateId - ID của template
               * @param payload - Variable values cho template rendering
               */
              async sendSMS(
                recipient: string,
                templateId: string,
                payload?: Record<string, any>,
              ): Promise<DispatchResult> {
                const template = this.templates.get(templateId);
                if (!template) {
                  throw new Error(`MDC-CP12-002: Template not found: ${templateId}`);
                }

                this.checkRateLimit(recipient, 'sms');
                const rendered = this.renderTemplate(template, payload || {});

                const result = await this.dispatchSMS(recipient, rendered);
                this.logDispatch(templateId, recipient, 'sms', result.status);
                return result;
              }

              /**
               * Gửi push notification.
               *
               * @param userId - User/device ID
               * @param templateId - ID của template
               * @param payload - Variable values cho template rendering
               */
              async sendPush(
                userId: string,
                templateId: string,
                payload?: Record<string, any>,
              ): Promise<DispatchResult> {
                const template = this.templates.get(templateId);
                if (!template) {
                  throw new Error(`MDC-CP12-002: Template not found: ${templateId}`);
                }

                this.checkRateLimit(userId, 'push');
                const rendered = this.renderTemplate(template, payload || {});

                const result = await this.dispatchPush(userId, rendered);
                this.logDispatch(templateId, userId, 'push', result.status);
                return result;
              }

              /** Lấy dispatch log gần đây. */
              getDispatchLog(limit = 100): DispatchResult[] {
                return this.dispatchLog.slice(-limit);
              }

              /** Kiểm tra rate limit per recipient per channel. */
              private checkRateLimit(recipient: string, channel: string): void {
                const key = `${recipient}:${channel}`;
                const now = Date.now();
                const record = this.rateLimits.get(key);

                if (!record || now - record.windowStart >= 3600000) {
                  this.rateLimits.set(key, { count: 1, windowStart: now });
                  return;
                }

                if (record.count >= 10) {
                  throw new Error(
                    `MDC-CP12-006: Rate limit exceeded for ${recipient} on ${channel}`,
                  );
                }

                record.count += 1;
              }

              /** Render template với variable interpolation. */
              private renderTemplate(
                template: NotificationTemplate,
                payload: Record<string, any>,
              ): { subject: string; bodyHtml: string; bodyText: string } {
                const replaceVars = (text: string) => {
                  return text.replace(/\\{\\{(\\w+)\\}\\}/g, (match, varName) => {
                    return payload[varName] !== undefined ? String(payload[varName]) : match;
                  });
                };
                return {
                  subject: replaceVars(template.subject),
                  bodyHtml: replaceVars(template.bodyHtml),
                  bodyText: replaceVars(template.bodyText),
                };
              }

              private async dispatchEmail(
                recipient: string,
                rendered: any,
              ): Promise<DispatchResult> {
                // TODO: Integrate với email provider (SMTP/SendGrid/SES)
                return { status: 'sent', recipient, channel: 'email', timestamp: new Date().toISOString() };
              }

              private async dispatchSMS(
                recipient: string,
                rendered: any,
              ): Promise<DispatchResult> {
                // TODO: Integrate với SMS provider (Twilio)
                return { status: 'sent', recipient, channel: 'sms', timestamp: new Date().toISOString() };
              }

              private async dispatchPush(
                userId: string,
                rendered: any,
              ): Promise<DispatchResult> {
                // TODO: Integrate với push provider (Firebase FCM)
                return { status: 'sent', recipient: userId, channel: 'push', timestamp: new Date().toISOString() };
              }

              private logDispatch(
                templateId: string,
                recipient: string,
                channel: string,
                status: string,
              ): void {
                this.dispatchLog.push({
                  status,
                  recipient,
                  channel,
                  timestamp: new Date().toISOString(),
                });
              }
            }
            ''')

    def generate_controller(self) -> str:
        """Generate NotificationController."""
        return textwrap.dedent('''\
            /**
             * Notification Controller - CP12: Notification & Communication
             *
             * REST endpoints cho notification operations.
             */

            import {
              Controller,
              Post,
              Get,
              Body,
              Query,
              BadRequestException,
            } from '@nestjs/common';
            import { NotificationService } from './notification.service';
            import { DispatchRequestDto, TemplateRequestDto } from './notification.dto';

            @Controller('notifications')
            export class NotificationController {
              constructor(private readonly notificationService: NotificationService) {}

              /**
               * Dispatch notification qua channel cụ thể.
               * Support: email, sms, push
               */
              @Post('dispatch')
              async dispatch(@Body() request: DispatchRequestDto) {
                try {
                  if (request.channel === 'email') {
                    const result = await this.notificationService.sendEmail(
                      request.recipient,
                      request.templateId,
                      request.payload,
                    );
                    return { ...result, message: 'Dispatch thành công' };
                  } else if (request.channel === 'sms') {
                    const result = await this.notificationService.sendSMS(
                      request.recipient,
                      request.templateId,
                      request.payload,
                    );
                    return { ...result, message: 'Dispatch thành công' };
                  } else if (request.channel === 'push') {
                    const result = await this.notificationService.sendPush(
                      request.recipient,
                      request.templateId,
                      request.payload,
                    );
                    return { ...result, message: 'Dispatch thành công' };
                  } else {
                    throw new BadRequestException(
                      `MDC-CP12-001: Channel không được hỗ trợ: ${request.channel}`,
                    );
                  }
                } catch (error) {
                  if (error.message.includes('MDC-')) {
                    throw new BadRequestException(error.message);
                  }
                  throw error;
                }
              }

              /** Liệt kê tất cả notification templates. */
              @Get('templates')
              async listTemplates() {
                return this.notificationService.listTemplates();
              }

              /** Đăng ký notification template mới. */
              @Post('templates')
              async registerTemplate(@Body() request: TemplateRequestDto) {
                this.notificationService.registerTemplate(request as any);
                return { status: 'registered', templateId: request.templateId };
              }

              /** Lấy dispatch log gần đây. */
              @Get('log')
              async getDispatchLog(@Query('limit') limit?: number) {
                const log = this.notificationService.getDispatchLog(limit || 50);
                return { log, total: log.length };
              }
            }
            ''')

    def generate_dto(self) -> str:
        """Generate DTOs cho notification."""
        return textwrap.dedent('''\
            /**
             * Notification DTOs - CP12: Request/Response schemas.
             */

            import { IsString, IsOptional, IsEnum, IsObject, IsArray } from 'class-validator';
            import { ApiProperty } from '@nestjs/swagger';

            export enum ChannelType {
              EMAIL = 'email',
              SMS = 'sms',
              PUSH = 'push',
              WEBHOOK = 'webhook',
              IN_APP = 'in_app',
            }

            export class DispatchRequestDto {
              @ApiProperty({ description: 'ID của template' })
              @IsString()
              templateId: string;

              @ApiProperty({ description: 'Người nhận (email, phone, user_id)' })
              @IsString()
              recipient: string;

              @ApiProperty({ enum: ChannelType, default: ChannelType.EMAIL })
              @IsEnum(ChannelType)
              channel: ChannelType;

              @ApiProperty({ required: false })
              @IsOptional()
              @IsObject()
              payload?: Record<string, any>;
            }

            export class TemplateRequestDto {
              @ApiProperty({ description: 'ID duy nhất của template' })
              @IsString()
              templateId: string;

              @ApiProperty({ enum: ChannelType })
              @IsEnum(ChannelType)
              channel: ChannelType;

              @ApiProperty({ required: false })
              @IsOptional()
              @IsString()
              subject?: string;

              @ApiProperty({ required: false })
              @IsOptional()
              @IsString()
              bodyHtml?: string;

              @ApiProperty({ required: false })
              @IsOptional()
              @IsString()
              bodyText?: string;

              @ApiProperty({ required: false })
              @IsOptional()
              @IsArray()
              variables?: string[];

              @ApiProperty({ default: 'en' })
              @IsOptional()
              @IsString()
              locale?: string;
            }
            ''')
