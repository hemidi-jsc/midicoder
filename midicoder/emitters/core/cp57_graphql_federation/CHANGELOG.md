# CP57: GraphQL Schema Federation — Changelog

## 1.0.0 (2026-05-26)

- Initial release
- Data models: FederationService, FederatedType, FederatedField, FederatedResolver, GatewayConfig
- Parser: GraphQLIR with from_dict + parse_to_ir
- Recipes: basic_federation_recipe, multi_service_recipe, full_federation_recipe
- Emitters: FastAPI, NestJS
- DSL NodeKind: FEDERATION_SERVICE, FEDERATED_TYPE, FEDERATED_RESOLVER, GATEWAY_CONFIG
- Pack emitter router: cp57.graphql_federation.fastapi, cp57.graphql_federation.nestjs
