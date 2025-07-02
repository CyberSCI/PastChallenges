FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build

WORKDIR /src

COPY ["VoterRegistryApi/VoterRegistryApi.csproj", "VoterRegistryApi/"]
RUN dotnet restore "./VoterRegistryApi/VoterRegistryApi.csproj"

COPY . .
WORKDIR "/src/VoterRegistryApi"
RUN dotnet build "./VoterRegistryApi.csproj" -c Release -o /app/build
RUN dotnet publish "./VoterRegistryApi.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:9.0

RUN apt-get update && \
    apt-get install -y python3 python3-pip postgresql-client tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages pytesseract pymupdf

WORKDIR /app
EXPOSE 8080

COPY --from=build /app/publish .
COPY documentscanner/documentscanner.py .

ENTRYPOINT ["dotnet", "VoterRegistryApi.dll"]