{
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        (.web_base_url + "/api/v1/vci/.well-known/contexts.json")
    ],
    "id": .vc_id,
    "type": ["VerifiableCredential", .issuer.credential_type],
    "issuer": .issuer.unique_issuer_id,
    "issuanceDate": .curr_datetime,
    "credentialSubject": {
        "vcVer": "VC-V1",
        "id": (.web_base_url  + "/api/v1/registry/group/" + (.group.id | tostring)),
        "fullName": [
            {
                "language": "eng",
                "value": (.group.name // null)
            }
        ],
        "addressLine1": (if .group.address.street_address then [
            {
                "language": "eng",
                "value": .group.address.street_address
            }
        ] else null end),
        "locality": (if .group.address.locality then [
            {
                "language": "eng",
                "value": .group.address.locality
            }
        ] else null end),
        "region": (if .group.address.region then [
            {
                "language": "eng",
                "value": .group.address.region
            }
        ] else null end),
        "postalCode": .group.address.postal_code,
        "face": .group.image,
        "UIN": (.group.ref_id // (.group.reg_ids["HOUSEHOLD ID"]?.value // (
            (.group.head.individual.reg_ids["NATIONAL ID"]?.value[0:5] | explode | reverse | implode)
            + (.group.head.individual.reg_ids["NATIONAL ID"]?.value[6:10] | explode | reverse| implode)
        ))),
        "headName": (if .group.head.individual.name then [
            {
                "language": "eng",
                "value": .group.head.individual.name
            }
        ] else null end),
        "headGender": (if .group.head.individual.gender then [
            {
                "language": "eng",
                "value": .group.head.individual.gender
            }
        ] else null end),
        "headDateOfBirth": (.group.head.individual.birthdate // null),
        "headNationalID": (.group.head.individual.reg_ids["NATIONAL ID"]?.value // null),
        "members": (
            .group.members | map(
                .individual.name +
                (if .individual.gender then " (" + .individual.gender + ") " else "" end) +
                (if .individual.birthdate then " (" + .individual.birthdate + ") " else "" end)
            )| join("\n")
        )
    }
}
