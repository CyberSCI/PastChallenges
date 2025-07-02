using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace VoterRegistryApi.Migrations
{
    /// <inheritdoc />
    public partial class Initial : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterDatabase()
                .Annotation("Npgsql:CollationDefinition:case_insensitive", "en-u-ks-primary,en-u-ks-primary,icu,False");

            migrationBuilder.CreateTable(
                name: "PollingStations",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    StreetNumber = table.Column<int>(type: "integer", nullable: false),
                    StreetName = table.Column<string>(type: "text", nullable: false),
                    City = table.Column<string>(type: "text", nullable: false),
                    State = table.Column<string>(type: "text", nullable: false),
                    PostalCode = table.Column<string>(type: "text", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PollingStations", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Advisories",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Message = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    Url = table.Column<string>(type: "text", nullable: true),
                    PollingStationId = table.Column<int>(type: "integer", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Advisories", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Advisories_PollingStations_PollingStationId",
                        column: x => x.PollingStationId,
                        principalTable: "PollingStations",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Streets",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    StreetName = table.Column<string>(type: "text", nullable: false, collation: "case_insensitive"),
                    City = table.Column<string>(type: "text", nullable: false, collation: "case_insensitive"),
                    State = table.Column<string>(type: "text", nullable: false, collation: "case_insensitive"),
                    PostalCode = table.Column<string>(type: "text", nullable: false, collation: "case_insensitive"),
                    PollingStationId = table.Column<int>(type: "integer", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Streets", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Streets_PollingStations_PollingStationId",
                        column: x => x.PollingStationId,
                        principalTable: "PollingStations",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "RegisteredPersons",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    FirstName = table.Column<string>(type: "text", nullable: false, collation: "case_insensitive"),
                    LastName = table.Column<string>(type: "text", nullable: false, collation: "case_insensitive"),
                    Birthdate = table.Column<DateOnly>(type: "date", nullable: false),
                    PhotoIdNumber = table.Column<string>(type: "text", nullable: false),
                    RegistrationNumber = table.Column<int>(type: "integer", nullable: true),
                    RegistrationFile = table.Column<string>(type: "text", nullable: true),
                    RegistrationFileMatchesInfo = table.Column<bool>(type: "boolean", nullable: false),
                    RegistrationFileReviewed = table.Column<bool>(type: "boolean", nullable: false),
                    RegistrationFileApproved = table.Column<bool>(type: "boolean", nullable: false),
                    RegistrationAddressNumber = table.Column<string>(type: "text", nullable: true),
                    RegistrationAddressStreetId = table.Column<int>(type: "integer", nullable: true),
                    RegistrationDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RegisteredPersons", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RegisteredPersons_Streets_RegistrationAddressStreetId",
                        column: x => x.RegistrationAddressStreetId,
                        principalTable: "Streets",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateIndex(
                name: "IX_Advisories_PollingStationId",
                table: "Advisories",
                column: "PollingStationId");

            migrationBuilder.CreateIndex(
                name: "IX_RegisteredPersons_PhotoIdNumber",
                table: "RegisteredPersons",
                column: "PhotoIdNumber",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_RegisteredPersons_RegistrationAddressStreetId",
                table: "RegisteredPersons",
                column: "RegistrationAddressStreetId");

            migrationBuilder.CreateIndex(
                name: "IX_RegisteredPersons_RegistrationNumber",
                table: "RegisteredPersons",
                column: "RegistrationNumber",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Streets_PollingStationId",
                table: "Streets",
                column: "PollingStationId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Advisories");

            migrationBuilder.DropTable(
                name: "RegisteredPersons");

            migrationBuilder.DropTable(
                name: "Streets");

            migrationBuilder.DropTable(
                name: "PollingStations");
        }
    }
}
