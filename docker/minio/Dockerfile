FROM golang:1.24-bookworm AS build
ENV CGO_ENABLED=0 GOBIN=/out
RUN go install github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z

FROM alpine:3.23
COPY --from=build /out/minio /usr/local/bin/minio
ENTRYPOINT ["minio"]
